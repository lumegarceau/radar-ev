import json, os, sys, time
import urllib.request, urllib.parse

KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"


def api(ruta, **p):
    q = urllib.parse.urlencode(p)
    hd = {"x-apisports-key": KEY}
    req = urllib.request.Request(BASE + ruta + "?" + q, headers=hd)
    time.sleep(0.3)
    j = json.load(urllib.request.urlopen(req, timeout=30))
    if j.get("errors"):
        print("Error API:", j["errors"])
        return []
    return j["response"]


def web(url):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        n = len(r.read())
        print("  " + url + " -> OK " + str(r.status) + ", " + str(n) + " bytes")
    except Exception as e:
        print("  " + url + " -> FALLA: " + str(e)[:80])


print("1) Cuotas de API-Football")
fx = api("/fixtures", league=140, season=2026, next=2)
mercados = {}
casas = set()
for f in fx:
    fid = f["fixture"]["id"]
    print(f["teams"]["home"]["name"], "v", f["teams"]["away"]["name"])
    for o in api("/odds", fixture=fid):
        for bk in o["bookmakers"]:
            casas.add(bk["name"])
            for b in bk["bets"]:
                n = b["name"]
                bajo = n.lower()
                for k in ("corner", "card", "shot", "foul"):
                    if k in bajo:
                        mercados.setdefault(n, set()).add(bk["name"])
print("Casas:", ", ".join(sorted(casas)) or "ninguna")
for n in sorted(mercados):
    print("  Mercado:", n, "->", ", ".join(sorted(mercados[n])))
if not mercados:
    print("  Sin mercados de corners/tarjetas/tiros/faltas")
print("")
print("2) Acceso a webs desde GitHub")
web("https://www.valueodds.net/")
web("https://www.winamax.es/")
web("https://www.oddschecker.com/")
