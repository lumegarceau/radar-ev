import difflib
import html
import json
import os
import time
import unicodedata
from datetime import date, timedelta
from rcommon import api

CORTE = str(date.today() - timedelta(days=5))
VARIANTES = {
    "sam": "samuel", "joe": "joseph", "joey": "joseph",
    "danny": "daniel", "dan": "daniel", "rob": "robert",
    "robbie": "robert", "bob": "robert", "leo": "leonardo",
    "ben": "benjamin", "tom": "thomas", "tommy": "thomas",
    "jim": "james", "jimmy": "james", "will": "william",
    "bill": "william", "matt": "matthew", "mike": "michael",
    "nick": "nicholas", "alex": "alexander", "andy": "andrew",
    "tony": "anthony", "chris": "christopher", "ed": "edward",
    "eddie": "edward", "fred": "frederick", "josh": "joshua",
    "zach": "zachary", "mo": "mohamed", "mohammed": "mohamed",
    "muhammad": "mohamed", "mohammad": "mohamed",
}


def norm(s):
    s = html.unescape(str(s or ""))
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(s.split())


def canon_nombre(n):
    t = norm(n).split()
    if t:
        t[0] = VARIANTES.get(t[0], t[0])
    return t


def jugadores_fixture(fid, viejo):
    f = "cache/p" + str(fid) + ".json"
    ant = None
    if os.path.exists(f):
        ant = json.load(open(f))
        if ant.get("v") == 2:
            return ant
    r = api("/fixtures/players", fixture=fid)
    if r is None:
        return ant or {}
    d = {"v": 2}
    for eq in r:
        lista = []
        for p in eq["players"]:
            st = (p.get("statistics") or [{}])[0]
            g = st.get("games") or {}
            sh = st.get("shots") or {}
            fo = st.get("fouls") or {}
            go = st.get("goals") or {}
            tk = st.get("tackles") or {}
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
                "tk": tk.get("total") or 0,
            })
        d[str(eq["team"]["id"])] = lista
    if len(d) == 3 or viejo:
        json.dump(d, open(f, "w"))
    return d


def plantilla(tid):
    f = "cache/sq" + str(tid) + ".json"
    if os.path.exists(f):
        try:
            d = json.load(open(f))
            if d.get("t", 0) > time.time() - 7 * 86400:
                return d.get("p", {})
        except Exception:
            pass
    r = api("/players/squads", team=tid)
    if r is None:
        return {}
    p = {}
    for eq in r:
        for pl in eq.get("players") or []:
            p[str(pl["id"])] = {
                "num": pl.get("number"),
                "pos": pl.get("position"),
            }
    json.dump({"t": time.time(), "p": p}, open(f, "w"))
    return p


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


def unico(c):
    if len(c) == 1:
        return c[0]
    return None


def compat(f1, f2):
    if f1 == f2:
        return True
    if len(f2) == 1 and f1[:1] == f2:
        return True
    if len(f1) == 1 and f2[:1] == f1:
        return True
    return difflib.SequenceMatcher(None, f1, f2).ratio() >= 0.75


def buscar(nombre, jug):
    full = norm(nombre)
    if not full:
        return None
    for pid, e in jug.items():
        if norm(e["n"]) == full:
            return pid
    t = canon_nombre(nombre)
    items = [(pid, canon_nombre(e["n"])) for pid, e in jug.items()]
    items = [(p, u) for p, u in items if u]
    c = [p for p, u in items if sorted(u) == sorted(t)]
    if c:
        return unico(c)
    f2 = " ".join(t)
    c = [p for p, u in items
         if difflib.SequenceMatcher(None, f2, " ".join(u)).ratio() >= 0.9]
    if c:
        return unico(c)
    if len(t) >= 2:
        c = [p for p, u in items if len(u) >= 2
             and (set(t) <= set(u) or set(u) <= set(t))]
        if c:
            return unico(c)
        unos = [p for p, u in items
                if len(u) == 1 and len(u[0]) >= 4 and u[0] in t]
        if len(unos) == 1:
            return unos[0]
    ape = t[-1]
    cs = [(p, u) for p, u in items if u[-1] == ape]
    if len(cs) == 1:
        p, u = cs[0]
        if len(t) == 1 or len(u) == 1:
            if len(ape) >= 4:
                return p
        elif len(ape) >= 6 or compat(t[0], u[0]):
            return p
    elif len(cs) > 1 and len(t) > 1:
        c = [p for p, u in cs if len(u) > 1 and compat(t[0], u[0])]
        return unico(c)
    return None


def prob_jug(juegos, stat, n, es_local):
    jj = [g for g in juegos if g["min"] > 0 and g.get(stat) is not None]
    N = len(jj)
    if N < 14:
        return None
    hits = sum(1 for g in jj if g[stat] >= n)
    cond = [g for g in jj if g["local"] == es_local][-10:]
    nc = len(cond)
    hc = sum(1 for g in cond if g[stat] >= n)
    ult = jj[-10:]
    h10 = sum(1 for g in ult if g[stat] >= n)
    if len(ult) < 10 or h10 < 7:
        return None
    if nc and hc < 0.7 * nc:
        return None
    p = hits / N
    if nc:
        w = nc / (nc + 10)
        p = ((1 - w) * p + w * hc / nc)
    return {"N": N, "hits": hits, "h10": h10, "hc": hc, "nc": nc,
            "prob": round(p, 3)}


def extras(juegos, stat):
    jj = [g for g in juegos if g["min"] > 0 and g.get(stat) is not None]
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
