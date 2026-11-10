import json, os, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KEY = os.environ.get("ODDSPAPI_KEY", "")
BASE = "https://api.oddspapi.io/v4"
BUSCA = ["betfair", "kirol", "retabet", "sportium", "marca", "juegging", "luckia", "codere"]


def api(path, **p):
    p["apiKey"] = KEY
    url = BASE + "/" + path + "?" + urllib.parse.urlencode(p)
    for i in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=180)
            return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(3); continue
            print("HTTP", e.code, path, e.read().decode("utf-8", "ignore")[:200]); return None
        except Exception as e:
            print("fallo", path, str(e)[:80]); return None


def lista(j):
    if isinstance(j, dict):
        j = j.get("data", j)
    if isinstance(j, dict):
        return list(j.values())
    return j or []


print("== A. Casas disponibles que encajan")
bk = lista(api("bookmakers"))
print("total casas:", len(bk))
for b in bk:
    s = json.dumps(b, ensure_ascii=False).lower()
    if any(k in s for k in BUSCA):
        print("  ", json.dumps(b, ensure_ascii=False)[:200])

print("== B. Partidos proximos (futbol)")
hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
fx = lista(api("fixtures", sportId=10, **{"from": str(hoy), "to": str(hoy + timedelta(days=3))}))
print("partidos:", len(fx))
cand = [f for f in fx if isinstance(f, dict)]
nl = [f for f in cand if any(x in json.dumps(f, ensure_ascii=False) for x in ("Italy", "Italia", "France", "Francia", "England", "Inglaterra"))]
elegido = (nl or cand)[:1]
cat = {}
for v in lista(api("markets")):
    if isinstance(v, dict):
        cat[str(v.get("marketId"))] = str(v.get("marketName", ""))
for f in elegido:
    fid = f.get("fixtureId")
    print("== C. Fixture", fid, f.get("participant1Name"), f.get("participant2Name"))
    od = api("odds", fixtureId=fid) or {}
    bo = od.get("bookmakerOdds") or {}
    print("casas con cuotas:", len(bo))
    for slug, d in sorted(bo.items()):
        mk = (d or {}).get("markets") or {}
        if any(k in slug.lower() for k in BUSCA) or True:
            nombres = [cat.get(str(m), str(m)) for m in mk]
            jug = [n for n in nombres if any(w in n.lower() for w in ("player", "jugador", "shots", "foul", "tackle"))]
            print("  %-22s mercados %3d | tipo jugador/props %3d" % (slug, len(mk), len(jug)))
            if any(k in slug.lower() for k in BUSCA):
                print("      ejemplos:", jug[:8])
