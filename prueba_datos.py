import json, os, sys, time
import urllib.parse, urllib.request

KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
LIGA = 140
TEMP = 2026
MAX_PARTIDOS = 2
PAUSA = float(os.environ.get("PAUSA", "0.3"))
LINEAS = [2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]
gasto = 0
os.makedirs("cache", exist_ok=True)


def api(ruta, **p):
    global gasto
    time.sleep(PAUSA)
    gasto += 1
    q = urllib.parse.urlencode(p)
    url = BASE + ruta + "?" + q
    hd = {"x-apisports-key": KEY}
    req = urllib.request.Request(url, headers=hd)
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
    f = "cache/c" + str(fid) + ".json"
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
    sin = 0
    lista = api("/fixtures", team=tid, last=20)
    lista = sorted(lista, key=lambda x: x["fixture"]["date"])
    for x in lista:
        est = x["fixture"]["status"]["short"]
        if est not in ("FT", "AET", "PEN"):
            continue
        h = x["teams"]["home"]["id"]
        a = x["teams"]["away"]["id"]
        c = corners(x["fixture"]["id"])
        rival = a
        if h != tid:
            rival = h
        if str(tid) in c and str(rival) in c:
            out.append({
                "local": h == tid,
                "pro": c[str(tid)],
                "contra": c[str(rival)],
            })
        else:
            sin += 1
    return out, sin


def media(h):
    if not h:
        return "-"
    return str(round(sum(x["pro"] for x in h) / len(h), 1))


def analizar(ht, hr, linea, es_local):
    n = len(ht)
    hits = sum(1 for x in ht if x["pro"] > linea)
    cond = [x for x in ht if x["local"] == es_local][-10:]
    nc = len(cond)
    hc = sum(1 for x in cond if x["pro"] > linea)
    p = hits / n
    if nc:
        w = nc / (nc + 10)
        p = ((1 - w) * p + w * hc / nc)
    nr = len(hr)
    r20 = sum(1 for x in hr if x["contra"] > linea)
    r10 = sum(1 for x in hr[-10:] if x["contra"] > linea)
    wr = 0.25
    if 5 <= r10 <= 7:
        wr = 0.15
    pf = ((1 - wr) * p + wr * r20 / nr)
    return {
        "linea": linea,
        "n": n,
        "l20": str(hits) + "/" + str(n),
        "cond": str(hc) + "/" + str(nc),
        "rival": str(r20) + "/" + str(nr),
        "prob": round(pf, 3),
        "hits": hits,
    }


partidos = api("/fixtures", league=LIGA, season=TEMP, next=MAX_PARTIDOS)
if not partidos:
    print("No hay partidos proximos.")
    sys.exit(0)

res = []
for p in partidos:
    loc = p["teams"]["home"]
    vis = p["teams"]["away"]
    hl, sl = historial(loc["id"])
    hv, sv = historial(vis["id"])
    nombre = loc["name"] + " v " + vis["name"]
    print("")
    print(nombre, p["fixture"]["date"][:16])
    print("  " + loc["name"] + ": " + str(len(hl)) + " partidos con datos"
          + " (" + str(sl) + " sin datos), corners medios " + media(hl))
    print("  " + vis["name"] + ": " + str(len(hv)) + " partidos con datos"
          + " (" + str(sv) + " sin datos), corners medios " + media(hv))
    if len(hl) < 5 or len(hv) < 5:
        print("  Sin datos suficientes")
        continue
    lados = [(loc, hl, hv, True), (vis, hv, hl, False)]
    for eq, h, ho, es_local in lados:
        for ln in LINEAS:
            r = analizar(h, ho, ln, es_local)
            if r["n"] < 10 or r["hits"] < 0.7 * r["n"]:
                continue
            r["equipo"] = eq["name"]
            r["partido"] = nombre
            r["hora"] = p["fixture"]["date"]
            res.append(r)
            cs = "visitante"
            if es_local:
                cs = "local"
            print("  " + eq["name"] + " +" + str(ln) + " corners"
                  + " | L20 " + r["l20"]
                  + " | " + cs + " " + r["cond"]
                  + " | rival " + r["rival"]
                  + " | prob " + str(round(r["prob"] * 100)) + "%")

json.dump(res, open("datos-prueba.json", "w"), ensure_ascii=False, indent=1)
print("")
print("Peticiones usadas:", gasto)
