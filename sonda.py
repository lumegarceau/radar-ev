import csv
import io
import json
import urllib.request
from datetime import date
import rvalue as rv

hoy = str(date.today())
txt = None
for u in ("http://api.clubelo.com/" + hoy, "https://api.clubelo.com/" + hoy):
    try:
        rq = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        txt = urllib.request.urlopen(rq, timeout=40).read().decode("utf-8")
        print("OK", u, "| bytes:", len(txt))
        break
    except Exception as e:
        print("FALLO", u, repr(e)[:150])
if not txt:
    print("sin acceso a ClubElo")
    raise SystemExit
filas = list(csv.DictReader(io.StringIO(txt)))
print("clubes:", len(filas), "| columnas:", list(filas[0].keys()))
for f in filas[:5]:
    print(f)
elo = {}
for f in filas:
    try:
        elo[f["Club"]] = (float(f["Elo"]), f["Country"], f["Level"])
    except Exception:
        pass
equipos = set()
try:
    d = json.load(open("radar-data.json"))
    for dia in d["days"]:
        for c in dia["candidatos"]:
            equipos.add(c["local"])
            equipos.add(c["visitante"])
except Exception as e:
    print("sin radar-data.json", repr(e)[:100])
print("equipos del radar:", len(equipos))
sin = []
dudosos = []
for e in sorted(equipos):
    mejor = None
    pm = 0
    for n in elo:
        s = rv.sim(e, n)
        if s > pm:
            pm = s
            mejor = n
    if pm >= 0.9:
        print("OK  ", e, "->", mejor, round(elo[mejor][0]), round(pm, 2))
    elif pm >= 0.6:
        dudosos.append((e, mejor, round(pm, 2)))
    else:
        sin.append(e)
print("\nDUDOSOS (0.6-0.9):", len(dudosos))
for x in dudosos:
    print("  ", x)
print("\nSIN CASAR:", len(sin))
for x in sin:
    print("  ", x)
for a, b in (("Benfica", "Lech Poznan"), ("Real Madrid", "Girona")):
    ea = [v for k, v in elo.items() if rv.sim(a, k) >= 0.9]
    eb = [v for k, v in elo.items() if rv.sim(b, k) >= 0.9]
    print(a, ea[:2], "|", b, eb[:2])
print("fin")
# fin
