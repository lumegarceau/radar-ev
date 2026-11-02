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
SIN_NULO = ("corners", "fouls", "shots")


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
            if not k:
                continue
            v = s["value"]
            if v is None:
                if k in SIN_NULO:
                    continue
                v = 0
            e[k] = v
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
        est = x["fixture"]["status"]["short"]
        if est not in ("FT", "AET", "PEN"):
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
        for k in SIN_NULO:
            if pro.get(k) == 0 and con.get(k) == 0:
                pro.pop(k, None)
                con.pop(k, None)
        pro["goals"] = gh if es_h else ga
        con["goals"] = ga if es_h else gh
        out.append({"local": es_h, "pro": pro, "contra": con})
    out.reverse()
    if agotado():
        return []
    return out


def tasa(vals, linea, sentido):
    if sentido == "under":
        return sum(1 for v in vals if v < linea)
    return sum(1 for v in vals if v > linea)


def mezcla(hits, n, hc, nc):
    p = hits / n
    if nc:
        w = nc / (nc + 10)
        p = (1 - w) * p + w * hc / nc
    return p


def analizar(h, hr, stat, linea, es_local, sentido="over"):
    a = [(x["local"], x["pro"][stat]) for x in h if stat in x["pro"]]
    b = [x["contra"][stat] for x in hr if stat in x["contra"]]
    n = len(a)
    nr = len(b)
    if n < 14 or nr < 10:
        return None
    hits = tasa([v for _, v in a], linea, sentido)
    cond = [v for lc, v in a if lc == es_local][-10:]
    nc = len(cond)
    hc = tasa(cond, linea, sentido)
    p = mezcla(hits, n, hc, nc)
    r20 = tasa(b, linea, sentido)
    r10 = tasa(b[-10:], linea, sentido)
    wr = 0.25
    if 5 <= r10 <= 7:
        wr = 0.15
    pf = (1 - wr) * p + wr * r20 / nr
    return {
        "n": n,
        "hits": hits,
        "l20": str(hits) + "/" + str(n),
        "cond": str(hc) + "/" + str(nc),
        "rival": str(r20) + "/" + str(nr),
        "prob": round(pf, 3),
    }


def tot_vals(h, stat):
    out = []
    for x in h:
        if stat in x["pro"] and stat in x["contra"]:
            out.append((x["local"], x["pro"][stat] + x["contra"][stat]))
    return out


def analizar_total(hl, hv, stat, linea, sentido):
    a = tot_vals(hl, stat)
    b = tot_vals(hv, stat)
    if len(a) < 14 or len(b) < 14:
        return None
    ha = tasa([v for _, v in a], linea, sentido)
    hb = tasa([v for _, v in b], linea, sentido)
    if ha < 0.7 * len(a) or hb < 0.7 * len(b):
        return None
    ca = [v for lc, v in a if lc][-10:]
    cb = [v for lc, v in b if not lc][-10:]
    hca = tasa(ca, linea, sentido)
    hcb = tasa(cb, linea, sentido)
    pa = mezcla(ha, len(a), hca, len(ca))
    pb = mezcla(hb, len(b), hcb, len(cb))
    l20 = "%d/%d y %d/%d" % (ha, len(a), hb, len(b))
    cond = "%d/%d y %d/%d" % (hca, len(ca), hcb, len(cb))
    return {
        "n": len(a),
        "hits": ha,
        "l20": l20,
        "cond": cond,
        "rival": None,
        "prob": round((pa + pb) / 2, 3),
        }
