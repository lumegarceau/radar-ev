import json
import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"


def get(path):
    h = {"User-Agent": UA, "Accept": "application/json,text/html"}
    req = urllib.request.Request(BASE + path, headers=h)
    r = urllib.request.urlopen(req, timeout=30)
    return r.read().decode("utf-8", "ignore")


home = get("/")
ids = re.findall(r'/partidos/[^"]*?-(\d+)"', home)
fid = ids[0] if ids else "19636778"
print("Fixture:", fid)

t = get("/api/v1/fixtures/" + fid + "/odds?format=compact")
print("Tamano respuesta:", len(t))
try:
    j = json.loads(t)
except Exception:
    print(t[:800])
    raise SystemExit
if isinstance(j, dict):
    print("Claves:", list(j.keys()))
print("--- Inicio ---")
print(json.dumps(j, ensure_ascii=False)[:1500])

pat = r"team_corners|team_cards|team_fouls|team_shots|corners_over|cards_over"
hits = []


def buscar(o, ruta):
    if len(hits) >= 6:
        return
    if isinstance(o, dict):
        txt = [v for v in o.values() if isinstance(v, str)]
        if any(re.search(pat, v, re.I) for v in txt):
            hits.append((ruta, json.dumps(o, ensure_ascii=False)[:900]))
        for k, v in o.items():
            if re.search(pat, str(k), re.I):
                hits.append((ruta + "/" + str(k), json.dumps(v, ensure_ascii=False)[:900]))
            buscar(v, ruta + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o[:80]):
            buscar(v, ruta + "/" + str(i))


buscar(j, "")
print("")
print("--- Mercados de equipo ---")
for r, s in hits[:6]:
    print(r)
    print(s)
    print("")

js = get("/assets/fixture.js?v=bdbcf40ca6")
i = js.find("team_corners")
print("--- Nombres de mercados (fixture.js) ---")
print(js[max(0, i - 200):i + 900].replace("\n", " "))

print("")
print("--- Direcciones de listado ---")
for m in sorted(set(re.findall(r"/api/v1/[a-zA-Z0-9_/\-\?=\$\{\}\.]{0,70}", home + js))):
    print(m)
