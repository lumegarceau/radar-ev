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
OTROS = ["foul", "shot", "tackle", "offside"]


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
if not fx:
    print("Sin partidos")
    raise SystemExit
fid = fx[0][1]["fixtureId"]
od = api("odds", fixtureId=fid) or {}
bo = od.get("bookmakerOdds") or {}
print("Fixture", fid, "casas", len(bo))

cat = {}
for k, v in items(api("markets")):
    if isinstance(v, dict):
        cat[str(v.get("marketId", k))] = v
nombres = {}
for mid, v in cat.items():
    nombres[mid] = str(v.get("marketName", ""))

print("")
print("A) MERCADOS DE EQUIPO POR CASA")
for s in CASAS:
    mer = ((bo.get(s) or {}).get("markets")) or {}
    c = {}
    for mid in mer:
        n = nombres.get(str(mid), "")
        if "Over Under Team" not in n:
            continue
        fam = n.split(" - ")[0]
        c[fam] = c.get(fam, 0) + 1
    print(" ", s, "| total", len(mer), "|", c)

print("")
print("B) FALTAS / TIROS / ENTRADAS")
vis = {}
for s in CASAS:
    mer = ((bo.get(s) or {}).get("markets")) or {}
    for mid in mer:
        n = nombres.get(str(mid), "")
        if any(f in n.lower() for f in OTROS):
            vis.setdefault(n, set()).add(s)
if not vis:
    print("  ninguno")
for n in sorted(vis)[:40]:
    print(" ", n, "|", len(vis[n]), "casas")

print("")
print("C) COMO SE DEFINE UNA LINEA")
objs = ["Corners - Over Under Team 1",
        "Bookings - Over Under Team 1"]
for obj in objs:
    n = 0
    for mid, v in cat.items():
        if v.get("marketName") == obj:
            print("CATALOGO", mid, json.dumps(v)[:420])
            n += 1
            if n >= 2:
                break

print("")
print("D) CUOTAS REALES DE CORNERS DEL EQUIPO 1")
for s in ("codere.es", "bet365", "winamax.es"):
    mer = ((bo.get(s) or {}).get("markets")) or {}
    n = 0
    for mid, m in mer.items():
        if nombres.get(str(mid)) != objs[0]:
            continue
        pr = {}
        for oid, o in (m.get("outcomes") or {}).items():
            p = (o.get("players") or {}).get("0") or {}
            pr[oid] = p.get("price")
        hc = cat[str(mid)].get("handicap")
        print(" ", s, mid, hc, pr)
        n += 1
        if n >= 5:
            break
print("Peticiones usadas:", usadas[0])
