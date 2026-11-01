import json
import os
from datetime import date, timedelta
from rcommon import api, agotado

CORTE = str(date.today() - timedelta(days=5))
STATS = {
    "Corner Kicks": "corners",
    "Fouls": "fouls",
    "Total Shots": "shots",
    "Shots on Goal": "sot",
    "Yellow Cards": "yc",
    "Red Cards": "rc",
}


def stats(fid, viejo):
    f = "cache/s" + str(fid) + ".json"
    if os.path.exists(f):
        return json.load(open(f))
    r = api("/fixtures/statistics", fixture=fid)
    if r is None:
        return {}
    d = {}
    for t in r:
        e = {}
        for s in t["statistics"]:
            k = STATS.get(s["type"])
            if k:
                e[k] = s["value"] or 0
        if "yc" in e:
            e["cards"] = e["yc"] + e.get("rc", 0)
        d[str(t["team"]["id"])] = e
    if len(d) == 2 or viejo:
        json.dump(d, open(f, "w"))
    return d


def historial(tid):
    out = []
    lista = api("/fixtures", team=tid, last=40) or []
    lista = sorted(lista, key=lambda x: x["fixture"]["date"])
    for x in reversed(lista):
        if len(out) >= 20:
            break
        if x["fixture"]["status"]["short"] not in ("FT", "AET", "PEN"):
            continue
        h = x["teams"]["home"]["id"]
        a = x["teams"]["away"]["id"]
        viejo = x["fixture"]["date"][:10] < CORTE
        c = stats(x["fixture"]["id"], viejo)
        es_h = h == tid
        rival = a
        if not es_h:
            rival = h
        if str(tid) not in c or str(rival) not in c:
            continue
        gh = x["goals"]["home"]
        ga = x["goals"]["away"]
        if gh is None or ga is None:
            continue
        pro = dict(c[str(tid)])
        con = dict(c[str(rival)])
        pro["goals"] = gh if es_h else ga
        con["goals"] = ga if es_h else gh
        out.append({"local": es_h, "pro": pro, "contra": con})
    out.reverse()
    if agotado():
        return []
    return out


def analizar(h, hr, stat, linea, es_local):
    a = [(x["local"], x["pro"][stat]) for x in h if stat in x["pro"]]
    b = [x["contra"][stat] for x in hr if stat in x["contra"]]
    n = len(a)
    nr = len(b)
    if n < 14 or nr < 10:
        return None
    hits = sum(1 for _, v in a if v > linea)
    cond = [v for lc, v in a if lc == es_local][-10:]
    nc = len(cond)
    hc = sum(1 for v in cond if v > linea)
    p = hits / n
    if nc:
        w = nc / (nc + 10)
        p = ((1 - w) * p + w * hc / nc)
    r20 = sum(1 for v in b if v > linea)
    r10 = sum(1 for v in b[-10:] if v > linea)
    wr = 0.25
    if 5 <= r10 <= 7:
        wr = 0.15
    pf = ((1 - wr) * p + wr * r20 / nr)
    return {
        "n": n,
        "hits": hits,
        "l20": str(hits) + "/" + str(n),
        "cond": str(hc) + "/" + str(nc),
        "rival": str(r20) + "/" + str(nr),
        "prob": round(pf, 3),
    }
