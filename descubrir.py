import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"


def get(path):
    h = {"User-Agent": UA, "Accept": "application/json,text/html"}
    req = urllib.request.Request(BASE + path, headers=h)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")


def partidos(o, out):
    if isinstance(o, dict):
        if "home_team" in o and "away_team" in o:
            out.append(o)
        for v in o.values():
            partidos(v, out)
    elif isinstance(o, list):
        for v in o:
            partidos(v, out)


st, home = get("/")
print("Portada:", st, len(home))
for m in re.finditer(r"api/v1/fixtures\?date", home):
    a = max(0, m.start() - 500)
    print("CONTEXTO PORTADA:")
    print(home[a:m.end() + 500].replace("\n", " "))
    break

hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
for i in range(6):
    f = str(hoy + timedelta(days=i))
    st, t = get("/api/v1/fixtures?date=" + f)
    print("")
    print("FECHA", f, "estado", st, "tamano", len(t))
    if st != 200:
        print("  respuesta:", t[:300])
        continue
    j = json.loads(t)
    if isinstance(j, dict):
        print("  claves:", list(j.keys()))
    lst = []
    partidos(j, lst)
    print("  partidos:", len(lst))
    for o in lst[:40]:
        comp = (o.get("competition") or {}).get("name", "?")
        a = (o.get("home_team") or {}).get("name", "?")
        b = (o.get("away_team") or {}).get("name", "?")
        print("   ", str(o.get("starts_at"))[:16], comp, "|", a, "v", b)
