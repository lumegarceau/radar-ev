import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rcommon import api, gasto
from rmodelo import historial, analizar
import rvalue as rv

MAD = ZoneInfo("Europe/Madrid")
TEMP = 2026
DIAS = 3
LIGAS = {
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
                    d = out.setdefault(("team_corners", lado, ln), {})
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


hoy = datetime.now(MAD).date()
fechas = [str(hoy + timedelta(days=i)) for i in range(DIAS + 1)]
vo = {}
for f in fechas:
    for o in rv.listar(f):
        vo[rv.idde(o)] = o
vo = list(vo.values())
print("valueodds:", len(vo), "partidos")

res = []
sin_par = []
con_vo = 0
rango = {"from": fechas[0], "to": fechas[-1]}
for lid, (pais, liga) in LIGAS.items():
    fx = api("/fixtures", league=lid, season=TEMP, **rango) or []
    print(liga, len(fx), "partidos")
    for x in fx:
        if x["fixture"]["status"]["short"] != "NS":
            continue
        loc = x["teams"]["home"]
        vis = x["teams"]["away"]
        dt = datetime.fromisoformat(x["fixture"]["date"]).astimezone(MAD)
        cu = {}
        o = rv.emparejar(loc["name"], vis["name"], dt, vo)
        if o:
            j = rv.vget("/api/v1/fixtures/" + str(rv.idde(o)) + "/odds?format=compact")
            if j:
                cu = rv.leer_cuotas(j)
                con_vo += 1
        else:
            sin_par.append(loc["name"] + " v " + vis["name"])
        cu = unir(cu, cuotas_af(x["fixture"]["id"]))
        if not cu:
            continue
        hl = hist(loc["id"])
        hv = hist(vis["id"])
        if not hl or not hv:
            continue
        for (tipo, lado, ln), q in sorted(cu.items()):
            if max(q.values()) < 1.40:
                continue
            stat = rv.MERC[tipo]
            es_local = lado == "home"
            eq = loc if es_local else vis
            h = hl if es_local else hv
            ho = hv if es_local else hl
            r = analizar(h, ho, stat, ln, es_local)
            if r is None or r["hits"] < 0.7 * r["n"]:
                continue
            txt = eq["name"] + " +" + str(ln).replace(".", ",")
            res.append({
                "pais": pais,
                "liga": liga,
                "fixture": x["fixture"]["id"],
                "equipo": eq["name"],
                "mercado": stat,
                "linea": ln,
                "local": loc["name"],
                "visitante": vis["name"],
                "hora": dt.strftime("%d/%m %H:%M"),
                "suceso": txt + " " + NOM[stat],
                "l20": r["l20"],
                "cond": r["cond"],
                "condTxt": "local" if es_local else "visitante",
                "rival": r["rival"],
                "prob": r["prob"],
                "cuotas": [{"b": b, "c": c} for b, c in q.items()],
            })

if res:
    ahora = datetime.now(MAD).isoformat(timespec="minutes")
    dia = {"fecha": str(hoy), "candidatos": res}
    out = {"updated_at": ahora, "days": [dia]}
    json.dump(out, open("radar-data.json", "w"), ensure_ascii=False)
else:
    print("Sin selecciones: no se toca radar-data.json")
print(len(res), "selecciones;", gasto[0], "peticiones API-Football")
print("Partidos con cuotas de valueodds:", con_vo)
print("Sin pareja en valueodds:", len(sin_par), sin_par[:6])
vt = sorted(rv.tipos.items(), key=lambda kv: -kv[1])
print("Mercados vistos:", vt[:40])
sa = sorted(rv.saltadas.items(), key=lambda kv: -kv[1])
print("Casas sin afiliado:", sa[:20])
