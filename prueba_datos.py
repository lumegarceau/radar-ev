import json, os, sys, time, urllib.parse, urllib.request

KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
LIGA, TEMP, MAX_PARTIDOS = 140, 2026, 2
PAUSA = float(os.environ.get("PAUSA", "0.3"))
LINEAS = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
gasto = 0
os.makedirs("cache", exist_ok=True)

def api(ruta, **p):
    global gasto
    time.sleep(PAUSA)
    gasto += 1
    url = BASE + ruta + "?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, headers={"x-apisports-key": KEY})
    try:
        j = json.load(urllib.request.urlopen(req, timeout=30))
    except Exception as e:
        print("Fallo de conexion:", e)
        sys.exit(1)
    if j.get("errors"):
        print("La API responde con un error:", j["errors"])
        sys.exit(1)
    return j["response"]

def corners(fid):
    f = "cache/c%s.json" % fid
    if os.path.exists(f):
        return json.load(open(f))
    d = {}
    for t in api("/fixtures/statistics", fixture=fid):
        for s in t["statistics"]:
            if s["type"] == "Corner Kicks":
                d[str(t["team"]["id"])] = s["value"] or 0
    if len(d) == 2:
        json.dump(d, open(f, "w"))
    return d

def historial(tid):
    out = []
    lista = sorted(api("/fixtures", team=tid, last=20), key=lambda x: x["fixture"]["date"])
    for x in lista:
        if x["fixture"]["status"]["short"] not in ("FT", "AET", "PEN"):
            continue
        h, a = x["teams"]["home"]["id"], x["teams"]["away"]["id"]
        c = corners(x["fixture"]["id"])
        rival = a if h == tid else h
        if str(tid) in c and str(rival) in c:
            out.append({"local": h == tid, "pro": c[str(tid)], "contra": c[str(rival)]})
    return out

def analizar(ht, hr, linea, es_local):
    n = len(ht)
    hits = sum(1 for x in ht if x["pro"] > linea)
    cond = [x for x in ht if x["local"] == es_local][-10:]
    nc = len(cond)
    hc = sum(1 for x in cond if x["pro"] > linea)
    p = hits / n
    if nc:
        w = nc / (nc + 10)
        p = (1 - w) * p +
