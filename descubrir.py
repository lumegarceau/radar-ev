import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"
QUIERO = [
    "player_tackles", "player_shots", "player_shots_on_target",
    "player_fouls_committed", "player_fouls_drawn", "player_saves",
    "total_corners", "total_cards", "total_fouls", "total_shots",
    "total_shots_on_target", "total_goals",
]


def get(path):
    h = {"User-Agent": UA, "Accept": "application/json"}
    req = urllib.request.Request(BASE + path, headers=h)
    r = urllib.request.urlopen(req, timeout=30)
    return json.loads(r.read().decode("utf-8", "ignore"))


def partidos(o, out):
    if isinstance(o, dict):
        if "home_team" in o and "away_team" in o:
            out.append(o)
        for v in o.values():
            partidos(v, out)
    elif isinstance(o, list):
        for v in o:
            partidos(v, out)


hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
vistos = {}
cuenta = {}
usados = 0
for i in range(4):
    f = str(hoy + timedelta(days=i))
    lst = []
    partidos(get("/api/v1/fixtures?date=" + f), lst)
    print(f, len(lst), "partidos")
    for o in lst:
        if usados >= 30 or len(vistos) == len(QUIERO):
            break
        fid = o.get("sportmonks_id") or o.get("id")
        nombre = (o.get("home_team") or {}).get("name", "?")
        try:
            od = get("/api/v1/fixtures/" + str(fid) + "/odds?format=compact")
        except Exception as e:
            print("fallo", fid, str(e)[:50])
            continue
        usados += 1
        for m in od.get("markets") or []:
            t = m.get("type")
            cuenta[t] = cuenta.get(t, 0) + 1
            if t in QUIERO and t not in vistos:
                vistos[t] = (nombre, m)

print("")
print("Fixtures revisados:", usados)
print("Encontrados:", sorted(vistos))
print("Faltan:", [t for t in QUIERO if t not in vistos])
for t in QUIERO:
    if t not in vistos:
        continue
    nombre, m = vistos[t]
    print("")
    print("=== " + t + " (" + nombre + ") ===")
    print("claves:", sorted(m.keys()))
    print(json.dumps(m, ensure_ascii=False)[:650])
