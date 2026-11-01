import json
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"


def get(path):
    h = {"User-Agent": UA, "Accept": "application/json"}
    req = urllib.request.Request(BASE + path, headers=h)
    r = urllib.request.urlopen(req, timeout=30)
    return r.read().decode("utf-8", "ignore")


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
for i in range(5):
    f = str(hoy + timedelta(days=i))
    t = get("/api/v1/fixtures?date=" + f)
    j = json.loads(t)
    print("")
    print("FECHA", f, "- tamano", len(t))
    if isinstance(j, dict):
        print("  claves:", list(j.keys()))
        for k, v in j.items():
            if not isinstance(v, (list, dict)):
                print("  ", k, "=", v)
        if "meta" in j:
            print("  meta:", json.dumps(j["meta"])[:300])
    if i == 1:
        print("  inicio respuesta:", t[:500])
    lst = []
    partidos(j, lst)
    print("  partidos:", len(lst))
    for o in lst[:30]:
        comp = (o.get("competition") or {}).get("name", "?")
        a = (o.get("home_team") or {}).get("name", "?")
        b = (o.get("away_team") or {}).get("name", "?")
        print("   ", str(o.get("starts_at"))[:16], comp, "|", a, "v", b)
