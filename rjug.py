import json
import os
import unicodedata
from datetime import date, timedelta
from rcommon import api

CORTE = str(date.today() - timedelta(days=5))


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(s.split())


def clave(n):
    t = norm(n).split()
    if len(t) < 2:
        return None
    return (t[0][0], t[-1])


def jugadores_fixture(fid, viejo):
    f = "cache/p" + str(fid) + ".json"
    if os.path.exists(f):
        return json.load(open(f))
    r = api("/fixtures/players", fixture=fid)
    if r is None:
        return {}
    d = {}
    for eq in r:
        lista = []
        for p in eq["players"]:
            st = (p.get("statistics") or [{}])[0]
            g = st.get("games") or {}
            sh = st.get("shots") or {}
            fo = st.get("fouls") or {}
            go = st.get("goals") or {}
            lista.append({
                "id": p["player"]["id"],
                "n": p["player"]["name"],
                "min": g.get("minutes") or 0,
                "pos": g.get("position"),
                "shots": sh.get("total") or 0,
                "sot": sh.get("on") or 0,
                "fouls": fo.get("committed") or 0,
                "drawn": fo.get("drawn") or 0,
                "saves": go.get("saves") or 0,
            })
        d[str(eq["team"]["id"])] = lista
    if len(d) == 2 or viejo:
        json.dump(d, open(f, "w"))
    return d


def hist_jug(tid):
    jug = {}
    usados = 0
    lista = api("/fixtures", team=tid, last=40) or []
    lista = sorted(lista, key=lambda x: x["fixture"]["date"])
    for x in reversed(lista):
        if usados >= 20:
            break
        if x["fixture"]["status"]["short"] not in ("FT", "AET", "PEN"):
            continue
        fid = x["fixture"]["id"]
        viejo = x["fixture"]["date"][:10] < CORTE
        d = jugadores_fixture(fid, viejo)
        mis = d.get(str(tid))
        if not mis:
            continue
        usados += 1
        es_h = x["teams"]["home"]["id"] == tid
        for p in mis:
            e = jug.setdefault(
                p["id"], {"n": p["n"], "pos": p["pos"], "g": []})
            e["g"].append(dict(p, local=es_h))
    for e in jug.values():
        e["g"].reverse()
    return jug, usados


def buscar(nombre, jug):
    full = norm(nombre)
    tok = full.split()
    if len(tok) < 2:
        return None
    k = (tok[0][0], tok[-1])
    a = []
    for pid, e in jug.items():
        if norm(e["n"]) == full:
            return pid
        if clave(e["n"]) == k:
            a.append(pid)
    if len(a) == 1:
        return a[0]
    if a:
        return None
    b = []
    for pid, e in jug.items():
        t = norm(e["n"]).split()
        if len(t) < 2:
            continue
        if t[0][0] == tok[0][0] and t[-1] in tok[1:]:
            b.append(pid)
    if len(b) == 1:
        return b[0]
    return None


def prob_jug(juegos, stat, n, es_local):
    jj = [g for g in juegos if g["min"] > 0]
    N = len(jj)
    if N < 14:
        return None
    hits = sum(1 for g in jj if g[stat] >= n)
    cond = [g for g in jj if g["local"] == es_local][-10:]
    nc = len(cond)
    hc = sum(1 for g in cond if g[stat] >= n)
    p = hits / N
    if nc:
        w = nc / (nc + 10)
        p = ((1 - w) * p + w * hc / nc)
    return {"N": N, "hits": hits, "hc": hc, "nc": nc,
            "prob": round(p, 3)}
