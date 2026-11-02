import json
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
}
memo = {}


def hist(tid):
    if tid not in memo:
        memo[tid] = rjug.hist_jug(tid)
    return memo[tid]


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


hoy = datetime.now(MAD).date()
fechas = [str(hoy + timedelta(days=i)) for i in range(DIAS + 1)]
rango = {"from": fechas[0], "to": fechas[-1]}
ts = datetime.now(MAD).timestamp()
try:
    wm = rw.partidos(SRIDS, ts, ts + (DIAS + 1) * 86400)
except Exception as e:
    print("winamax fallo general", repr(e)[:150])
    raise SystemExit
print("winamax:", len(wm), "partidos")

nuevos = []
sin = []
emp = 0
n_part = 0
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
        if not w:
            continue
        n_part += 1
        jl, nl = hist(loc["id"])
        jv, nv = hist(vis["id"])
        print(loc["name"], "v", vis["name"], "| partidos con datos",
              nl, nv, "| cuotas jugador", len(w["jugador"]))
        for stat, nom, sr, lado, n, c in w["jugador"]:
            if c < 1.40:
                continue
            es_local = lado == "home"
            jug = jl if es_local else jv
            pid = rjug.buscar(nom, jug)
            if pid is None:
                sin.append(nom)
                continue
            e = jug[pid]
            if stat == "saves" and e["pos"] != "G":
                continue
            r = rjug.prob_jug(e["g"], stat, n, es_local)
            if r is None or r["hits"] < 0.7 * r["N"]:
                continue
            emp += 1
            eq = loc if es_local else vis
            suc = nom + " " + str(n) + "+ " + NOM[stat]
            nuevos.append({
                "tipo": "jugador",
                "pais": pais,
                "liga": liga,
                "fixture": x["fixture"]["id"],
                "equipo": eq["name"],
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
                "cuotas": [{"b": "Winamax", "c": c}],
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
json.dump(data, open(fn, "w"), ensure_ascii=False)
print("partidos con Winamax:", n_part)
print("props de jugador:", len(nuevos))
print("jugadores sin emparejar:", len(sin), sin[:12])
print("peticiones API-Football:", gasto[0])
