import difflib
import json
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rcommon import api, gasto
import rvalue as rv
import rwina as rw
import rjug

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
SRIDS = set([
    "sr:tournament:8", "sr:tournament:54", "sr:tournament:17",
    "sr:tournament:18", "sr:tournament:23", "sr:tournament:34",
    "sr:tournament:35", "sr:tournament:37", "sr:tournament:238",
])
NOM = {
    "shots": "remates",
    "sot": "remates a puerta",
    "fouls": "faltas cometidas",
    "drawn": "faltas recibidas",
    "saves": "paradas",
    "tk": "entradas",
}
memo = {}
sqm = {}


def hist(tid):
    if tid not in memo:
        memo[tid] = rjug.hist_jug(tid)
    return memo[tid]


def squad(tid):
    if tid not in sqm:
        sqm[tid] = rjug.plantilla(tid)
    return sqm[tid]


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


def leer_winamax(ts):
    for i in range(3):
        try:
            return rw.partidos(SRIDS, ts, ts + (DIAS + 1) * 86400)
        except Exception as e:
            print("winamax intento", i + 1, "fallo", repr(e)[:100])
            time.sleep(30)
    return None


hoy = datetime.now(MAD).date()
fechas = [str(hoy + timedelta(days=i)) for i in range(DIAS + 1)]
rango = {"from": fechas[0], "to": fechas[-1]}
vo = {}
for f in fechas:
    for o in rv.listar(f):
        vo[rv.idde(o)] = o
vo = list(vo.values())
print("valueodds:", len(vo), "partidos")
ts = datetime.now(MAD).timestamp()
wm = leer_winamax(ts)
wina_ok = wm is not None
if not wina_ok:
    wm = []
    print("SIN WINAMAX en esta pasada: solo valueodds")
print("winamax:", len(wm), "partidos")

nuevos = []
sin_u = {}
sin_v = set()
con_u = set()
n_part = 0
n_vo = 0
for lid, (pais, liga) in LIGAS.items():
    fx = api("/fixtures", league=lid, season=TEMP, **rango) or []
    for x in fx:
        if x["fixture"]["status"]["short"] != "NS":
            continue
        loc = x["teams"]["home"]
        vis = x["teams"]["away"]
        iso = x["fixture"]["date"]
        dt = datetime.fromisoformat(iso).astimezone(MAD)
        w = buscar_wina(loc["name"], vis["name"], dt, wm)
        pv = {}
        o = rv.emparejar(loc["name"], vis["name"], dt, vo)
        if o:
            ruta = "/api/v1/fixtures/" + str(rv.idde(o))
            j = rv.vget(ruta + "/odds?format=compact")
            if j:
                pv = rv.leer(j)[2]
        if not w and not pv:
            continue
        n_part += 1
        jl, nl = hist(loc["id"])
        jv, nv = hist(vis["id"])
        cu = {}
        disp = {}
        if w:
            for stat, nom, sr, lado, n, c in w["jugador"]:
                jug = jl if lado == "home" else jv
                eqx = loc if lado == "home" else vis
                pid = rjug.buscar(nom, jug)
                if pid is None:
                    sin_u[(eqx["name"], nom)] = jug
                    continue
                disp.setdefault(pid, nom)
                d = cu.setdefault((stat, pid, n, lado), {})
                if c > d.get("Winamax", 0):
                    d["Winamax"] = c
        for (stat, nom, ln), q in pv.items():
            n = int(ln + 0.5)
            a = rjug.buscar(nom, jl)
            b = rjug.buscar(nom, jv)
            if (a is None) == (b is None):
                sin_v.add(nom)
                continue
            lado = "home"
            pid = a
            if a is None:
                lado = "away"
                pid = b
            n_vo += 1
            disp.setdefault(pid, nom)
            d = cu.setdefault((stat, pid, n, lado), {})
            for casa, c in q.items():
                if c > d.get(casa, 0):
                    d[casa] = c
        for key in sorted(cu, key=str):
            stat, pid, n, lado = key
            q = cu[key]
            if max(q.values()) < 1.40:
                continue
            es_local = lado == "home"
            jug = jl if es_local else jv
            eq = loc if es_local else vis
            e = jug[pid]
            con_u.add((eq["name"], pid))
            if stat == "saves" and e["pos"] != "G":
                continue
            r = rjug.prob_jug(e["g"], stat, n, es_local)
            if r is None or r["hits"] < 0.7 * r["N"]:
                continue
            ex = rjug.extras(e["g"], stat)
            sq = squad(eq["id"])
            num = (sq.get(str(pid)) or {}).get("num")
            nombre = disp.get(pid, e["n"])
            suc = nombre + " " + str(n) + "+ " + NOM[stat]
            nuevos.append({
                "tipo": "jugador",
                "pais": pais,
                "liga": liga,
                "lid": lid,
                "fixture": x["fixture"]["id"],
                "equipo": eq["name"],
                "tid": eq["id"],
                "hid": loc["id"],
                "aid": vis["id"],
                "pid": pid,
                "num": num,
                "pos": e["pos"],
                "mercado": stat,
                "linea": n,
                "local": loc["name"],
                "visitante": vis["name"],
                "hora": dt.strftime("%d/%m %H:%M"),
                "suceso": suc,
                "l20": str(r["hits"]) + "/" + str(r["N"]),
                "cond": str(r["hc"]) + "/" + str(r["nc"]),
                "condTxt": "local" if es_local else "visitante",
                "rival": None,
                "prob": r["prob"],
                "serie": ex["serie"],
                "media": ex["media"],
                "minmed": ex["minmed"],
                "por90": ex["por90"],
                "tit": ex["tit"],
                "cuotas": [{"b": b, "c": c} for b, c in q.items()],
            })

fn = "radar-data.json"
try:
    data = json.load(open(fn))
except Exception:
    data = None
ahora = datetime.now(MAD).isoformat(timespec="minutes")
if not data or not data.get("days"):
    dia = {"fecha": str(hoy), "candidatos": []}
    data = {"updated_at": ahora, "days": [dia]}
dia = data["days"][-1]
dia["candidatos"] = [c for c in dia["candidatos"]
                     if c.get("tipo") != "jugador"] + nuevos
data["updated_at"] = ahora
data["props_ok"] = wina_ok
json.dump(data, open(fn, "w"), ensure_ascii=False)
por = {}
for c in nuevos:
    por[c["mercado"]] = por.get(c["mercado"], 0) + 1
print("pasada completa (con Winamax):", wina_ok)
print("partidos con cuotas de jugador:", n_part)
print("props de jugador:", len(nuevos), por)
print("con dorsal:", sum(1 for c in nuevos if c.get("num")))
print("cuotas de valueodds emparejadas:", n_vo)
print("jugadores emparejados:", len(con_u))
print("sin emparejar Winamax:", len(sin_u))
for (eqn, nom), jug in list(sin_u.items())[:12]:
    alvo = rjug.norm(nom)
    cands = sorted(
        jug.values(),
        key=lambda e: -difflib.SequenceMatcher(
            None, alvo, rjug.norm(e["n"])).ratio())[:2]
    print("  ", eqn, "|", nom, "->", [c["n"] for c in cands])
print("sin emparejar valueodds:", len(sin_v), sorted(sin_v)[:15])
print("peticiones API-Football:", gasto[0])
