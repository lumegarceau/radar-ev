import difflib
import html
import json
import os
import unicodedata
from datetime import date, timedelta
from rcommon import api

CORTE = str(date.today() - timedelta(days=5))


def norm(s):
    s = html.unescape(str(s or ""))
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(s.split())


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
                "sub": g.get("substitute"),
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


def partes(n):
    t = norm(n).split()
    if not t:
        return "", [], ""
    return t[0], t[1:], "".join(t[1:])


def mismo_nombre(g1, g2):
    if len(g1) == 1 or len(g2) == 1:
        return g1[:1] == g2[:1]
    r = difflib.SequenceMatcher(None, g1, g2).ratio()
    return r >= 0.75


def mismo_apellido(s1, s2, t1, t2):
    if not s1 or not s2:
        return False
    if s1 == s2:
        return True
    corto = min(len(s1), len(s2))
    if corto >= 5 and (s1.startswith(s2) or s2.startswith(s1)):
        return True
    if t1 and t2 and (set(t1) <= set(t2) or set(t2) <= set(t1)):
        return True
    r = difflib.SequenceMatcher(None, s1, s2).ratio()
    return r >= 0.88 or (corto >= 8 and r >= 0.85)


def buscar(nombre, jug):
    full = norm(nombre)
    tok = full.split()
    if not tok:
        return None
    for pid, e in jug.items():
        if norm(e["n"]) == full:
            return pid
    g, t, s = partes(nombre)
    cand = []
    for pid, e in jug.items():
        ng = norm(e["n"]).split()
        if not ng:
            continue
        if len(ng) == 1:
            if len(tok) > 1 and ng[0] in tok:
                cand.append(pid)
            continue
        if len(tok) == 1:
            if tok[0] in ng:
                cand.append(pid)
            continue
        g2, t2, s2 = partes(e["n"])
        if not mismo_nombre(g, g2):
            continue
        if mismo_apellido(s, s2, t, t2):
            cand.append(pid)
    if len(cand) == 1:
        return cand[0]
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


def extras(juegos, stat):
    jj = [g for g in juegos if g["min"] > 0]
    vacio = {"serie": [], "media": None, "minmed": None,
             "por90": None, "tit": None}
    if not jj:
        return vacio
    vals = [g[stat] for g in jj]
    mins = sum(g["min"] for g in jj)
    por90 = None
    if mins > 0:
        por90 = round(sum(vals) * 90 / mins, 2)
    fl = [g for g in jj if g.get("sub") is not None]
    tit = None
    if len(fl) >= 5:
        tit = round(100 * sum(1 for g in fl if g["sub"] is False) / len(fl))
    return {
        "serie": list(reversed(vals))[:10],
        "media": round(sum(vals) / len(vals), 2),
        "minmed": round(mins / len(jj)),
        "por90": por90,
        "tit": tit,
            }
