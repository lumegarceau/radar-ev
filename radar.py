import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rcommon import api, gasto
from rmodelo import historial, analizar, analizar_total
import rvalue as rv
import rwina as rw

MAD = ZoneInfo("Europe/Madrid")
TEMP = 2026
DIAS = 3
LIGAS = {
    2: ("Europa", "Champions League"),
    3: ("Europa", "Europa League"),
    140: ("España", "LaLiga"),
    141: ("España", "Segunda División"),
    39: ("Inglaterra", "Premier League"),
    40: ("Inglaterra", "Championship"),
    135: ("Italia", "Serie A"),
    61: ("Francia", "Ligue 1"),
    78: ("Alemania", "Bundesliga"),
    88: ("Países Bajos", "Eredivisie"),
    94: ("Portugal", "Primeira Liga"),
}
SRIDS = set([
    "sr:tournament:8", "sr:tournament:54", "sr:tournament:17",
    "sr:tournament:18", "sr:tournament:23", "sr:tournament:34",
    "sr:tournament:35", "sr:tournament:37", "sr:tournament:238",
    "sr:tournament:7", "sr:tournament:679",
])
NOM = {
    "corners": "córners",
    "cards": "tarjetas",
    "fouls": "faltas",
    "shots": "tiros",
    "sot": "tiros a puerta",
    "goals": "goles",
}
memo = {}


def hist(tid):
    if tid not in memo:
        memo[tid] = historial(tid)
    return memo[tid]


def fl(n):
    return str(n).replace(".", ",")


def cuotas_af(fid):
    out = {}
    for o in api("/odds", fixture=fid) or []:
        for bk in o["bookmakers"]:
            can = rv.canon(bk["name"])
            if not can:
                continue
            for b in bk["bets"]:
                if b["name"] == "Home Corners Over/Under":
                    lado = "home"
                elif b["name"] == "Away Corners Over/Under":
                    lado = "away"
                else:
                    continue
                for v in b["values"]:
                    t = str(v["value"]).split()
                    if len(t) != 2 or t[0] != "Over":
                        continue
                    try:
                        ln = float(t[1])
                        c = float(v["odd"])
                    except Exception:
                        continue
                    if abs(ln % 1 - 0.5) > 0.001:
                        continue
                    k = ("eq", "corners", lado, ln, "over")
                    d = out.setdefault(k, {})
                    if c > d.get(can, 0):
                        d[can] = c
    return out


def unir(a, b):
    for k, q in b.items():
        d = a.setdefault(k, {})
        for casa, c in q.items():
            if c > d.get(casa, 0):
                d[casa] = c
    return a


def desde_vo(eqv, totv):
    cu = {}
    for (stat, lado, ln, s), q in eqv.items():
        cu[("eq", stat, lado, ln, s)] = dict(q)
    for (stat, ln, s), q in totv.items():
        cu[("tot", stat, "total", ln, s)] = dict(q)
    return cu


def buscar_wina(loc, vis, dt, lista):
    mejor = None
    pm = 0
    for w in lista:
        if not w.get("inicio"):
            continue
        if abs(w["inicio"] - dt.timestamp()) > 10800:
            continue
        s1 = rv.sim(loc, w["c1"])
        s2 = rv.sim(vis, w["c2"])
        if min(s1, s2) < 0.5:
            continue
        p = (s1 + s2) / 2
        if p > pm:
            mejor = w
            pm = p
    if pm >= 0.62:
        return mejor
    return None


def anadir_wina(cu, w):
    for stat, lado, ln, c, s in w["equipo"]:
        d = cu.setdefault(("eq", stat, lado, ln, s), {})
        if c > d.get("Winamax", 0):
            d["Winamax"] = c
    for stat, ln, c, s in w["total"]:
        d = cu.setdefault(("tot", stat, "total", ln, s), {})
        if c > d.get("Winamax", 0):
            d["Winamax"] = c


hoy = datetime.now(MAD).date()
fechas = [str(hoy + timedelta(days=i)) for i in range(DIAS + 1)]
vo = {}
for f in fechas:
    for o in rv.listar(f):
        vo[rv.idde(o)] = o
vo = list(vo.values())
print("valueodds:", len(vo), "partidos")

ts = datetime.now(MAD).timestamp()
try:
    wm = rw.partidos(SRIDS, ts, ts + (DIAS + 1) * 86400)
except Exception as e:
    print("winamax fallo general", repr(e)[:150])
    wm = []
ne = sum(len(w["equipo"]) for w in wm)
nt = sum(len(w["total"]) for w in wm)
print("winamax:", len(wm), "partidos;", ne, "de equipo;", nt, "de totales")

res = []
sin_par = []
con_vo = 0
con_wi = 0
rango = {"from": fechas[0], "to": fechas[-1]}
for lid, (pais, liga) in LIGAS.items():
    fx = api("/fixtures", league=lid, season=TEMP, **rango) or []
    print(liga, len(fx), "partidos")
    for x in fx:
        if x["fixture"]["status"]["short"] != "NS":
            continue
        loc = x["teams"]["home"]
        vis = x["teams"]["away"]
        iso = x["fixture"]["date"]
        dt = datetime.fromisoformat(iso).astimezone(MAD)
        cu = {}
        o = rv.emparejar(loc["name"], vis["name"], dt, vo)
        if o:
            ruta = "/api/v1/fixtures/" + str(rv.idde(o))
            j = rv.vget(ruta + "/odds?format=compact")
            if j:
                eqv, totv, _ = rv.leer(j)
                cu = desde_vo(eqv, totv)
                con_vo += 1
        else:
            sin_par.append(loc["name"] + " v " + vis["name"])
        cu = unir(cu, cuotas_af(x["fixture"]["id"]))
        w = buscar_wina(loc["name"], vis["name"], dt, wm)
        if w:
            con_wi += 1
            anadir_wina(cu, w)
        if not cu:
            continue
        hl = hist(loc["id"])
        hv = hist(vis["id"])
        if not hl or not hv:
            continue
        orden = sorted(cu.items(), key=lambda kv: str(kv[0]))
        for (kind, stat, lado, ln, sent), q in orden:
            if max(q.values()) < 1.40:
                continue
            if kind == "eq":
                es_local = lado == "home"
                eqp = loc if es_local else vis
                h = hl if es_local else hv
                ho = hv if es_local else hl
                r = analizar(h, ho, stat, ln, es_local, sent)
                if r is None:
                    continue
                vals = [y["pro"][stat] for y in h if stat in y["pro"]]
                serie = list(reversed(vals))[:10]
                media = round(sum(vals) / len(vals), 2)
                nombre = eqp["name"]
                tid = eqp["id"]
                cond_txt = "local" if es_local else "visitante"
            else:
                r = analizar_total(hl, hv, stat, ln, sent)
                if r is None:
                    continue
                serie = []
                media = None
                nombre = "Total del partido"
                tid = None
                cond_txt = "local y visitante"
            frase = " +" if sent == "over" else " menos de "
            suceso = nombre + frase + fl(ln) + " " + NOM[stat]
            res.append({
                "tipo": "equipo" if kind == "eq" else "total",
                "sentido": sent,
                "pais": pais,
                "liga": liga,
                "lid": lid,
                "fixture": x["fixture"]["id"],
                "equipo": nombre,
                "tid": tid,
                "hid": loc["id"],
                "aid": vis["id"],
                "mercado": stat,
                "linea": ln,
                "local": loc["name"],
                "visitante": vis["name"],
                "hora": dt.strftime("%d/%m %H:%M"),
                "suceso": suceso,
                "l20": r["l20"],
                "l10": r.get("l10"),
                "cond": r["cond"],
                "condTxt": cond_txt,
                "rival": r.get("rival"),
                "prob": r["prob"],
                "serie": serie,
                "media": media,
                "cuotas": [{"b": b, "c": c} for b, c in q.items()],
            })

if res:
    ahora = datetime.now(MAD).isoformat(timespec="minutes")
    dia = {"fecha": str(hoy), "candidatos": res}
    out = {"updated_at": ahora, "days": [dia]}
    json.dump(out, open("radar-data.json", "w"), ensure_ascii=False)
else:
    print("Sin selecciones: no se toca radar-data.json")
cnt = {}
for c in res:
    k = c["tipo"] + "_" + c["sentido"]
    cnt[k] = cnt.get(k, 0) + 1
print(len(res), "selecciones;", gasto[0], "peticiones API-Football")
print("Por tipo:", cnt)
print("Partidos con cuotas de valueodds:", con_vo)
print("Partidos con cuotas de Winamax:", con_wi)
print("Sin pareja en valueodds:", len(sin_par), sin_par[:6])
print("Tarjetas omitidas (formato distinto):", rv.omitidas["tarjetas"])
sa = sorted(rv.saltadas.items(), key=lambda kv: -kv[1])
print("Casas sin afiliado:", sa[:20])
