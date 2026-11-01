import json, os
from datetime import date, timedelta
from rcommon import api

CORTE = str(date.today() - timedelta(days=5))


def corners(fid, viejo):
    f = "cache/c" + str(fid) + ".json"
    if os.path.exists(f):
        return json.load(open(f))
    r = api("/fixtures/statistics", fixture=fid)
    if r is None:
        return {}
    d = {}
    for t in r:
        for s in t["statistics"]:
            if s["type"] == "Corner Kicks":
                d[str(t["team"]["id"])] = s["value"] or 0
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
        c = corners(x["fixture"]["id"], viejo)
        rival = a
        if h != tid:
            rival = h
        if str(tid) in c and str(rival) in c:
            out.append({
                "local": h == tid,
                "pro": c[str(tid)],
                "contra": c[str(rival)],
            })
    out.reverse()
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
        p = ((1 - w) * p + w * hc / nc)
    nr = len(hr)
    r20 = sum(1 for x in hr if x["contra"] > linea)
    r10 = sum(1 for x in hr[-10:] if x["contra"] > linea)
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
