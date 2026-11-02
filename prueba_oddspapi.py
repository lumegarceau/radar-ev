import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KEY = os.environ.get("ODDSPAPI_KEY", "")
BASE = "https://api.oddspapi.io/v4"
UA = "Mozilla/5.0 Chrome/120 Safari/537.36"
usadas = [0]
CASAS = [
    "1xbet", "888sport.es", "bet365",
    "betfair.es", "betsson", "betway.es",
    "bwin.es", "codere.es", "interwetten",
    "paf.es", "williamhill", "winamax.es",
]
FAM = ["corner", "card", "booking", "foul",
       "shot", "tackle"]


def api(path, **p):
    p["apiKey"] = KEY
    q = urllib.parse.urlencode(p)
    url = BASE + "/" + path + "?" + q
    for i in range(3):
        usadas[0] += 1
        h = {"User-Agent": UA}
        req = urllib.request.Request(url, headers=h)
        try:
            r = urllib.request.urlopen(req, timeout=180)
            return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "ignore")
            if e.code == 429:
                print("429, espero")
                time.sleep(3)
                continue
            print("HTTP", e.code, path, txt[:200])
            return None
        except Exception as e:
            print("fallo", path, str(e)[:80])
            return None
    return None


def items(j):
    if isinstance(j, dict):
        j = j.get("data", j)
    out = []
    if isinstance(j, dict):
        for k, v in j.items():
            out.append((str(k), v))
    elif isinstance(j, list):
        for v in j:
            out.append(("", v))
    return out


hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
fin = hoy + timedelta(days=3)
rango = {"from": str(hoy), "to": str(fin)}
j = api("fixtures", sportId=10,
        tournamentId=8, **rango)
fx = items(j)
print("Partidos LaLiga:", len(fx))
if not fx:
    raise SystemExit
fid = fx[0][1]["fixtureId"]
print("Fixture:", fid)

od = api("odds", fixtureId=fid) or {}
bo = od.get("bookmakerOdds") or {}
print("Casas con cuotas:", len(bo))

nombres = {}
for k, v in items(api("markets")):
    if not isinstance(v, dict):
        continue
    mid = str(v.get("marketId", k))
    nombres[mid] = str(v.get("marketName", ""))
print("Mercados en catalogo:", len(nombres))

print("")
print("MERCADOS POR CASA")
for s in CASAS:
    if s not in bo:
        print(" ", s, "-> sin cuotas en este partido")
        continue
    mer = (bo[s] or {}).get("markets") or {}
    cuenta = {}
    for mid in mer:
        n = nombres.get(str(mid), "").lower()
        for fam in FAM:
            if fam in n:
                cuenta[fam] = cuenta.get(fam, 0) + 1
    print(" ", s, "| total", len(mer), "|", cuenta)

vis = {}
ejemplo = None
for s in CASAS:
    mer = ((bo.get(s) or {}).get("markets")) or {}
    for mid, m in mer.items():
        n = nombres.get(str(mid), "")
        if not any(f in n.lower() for f in FAM):
            continue
        vis.setdefault(n, set()).add(s)
        if ejemplo is None and "corner" in n.lower():
            ejemplo = (s, mid, n, m)

print("")
print("NOMBRES DE MERCADO (corners, tarjetas...)")
for n in sorted(vis)[:70]:
    print(" ", n, "|", len(vis[n]), "casas")

if ejemplo:
    print("")
    print("EJEMPLO:", ejemplo[0], ejemplo[1], ejemplo[2])
    print(json.dumps(ejemplo[3])[:700])
print("")
print("Peticiones usadas:", usadas[0])
