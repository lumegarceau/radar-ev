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
ESPECIAL = str.maketrans({
    "ø": "o", "đ": "d", "ł": "l", "ß": "ss", "æ": "ae", "œ": "oe",
    "ı": "i", "ð": "d", "þ": "th",
})


def arreglar(s):
    if "Ã" in s or "Ä" in s or "Å" in s:
        try:
            return s.encode("latin-1").decode("utf-8")
        except Exception:
            return s
    return s


def norm(s):
    s = arreglar(html.unescape(str(s or "")))
    s = unicodedata.normalize("NFD", s.lower().translate(ESPECIAL))
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


HIST_MAX = 40
PARAR = 11
MIN_JUEGO = 45


def calif(p):
    m = p.get("min") or 0
    s = p.get("sub")
    if s is False:
        return m >= MIN_JUEGO
    if s is None:
        return m >= 60
    return False


def validos(juegos, stat):
    jj = [g for g in juegos if calif(g) and g.get(stat) is not None]
    return jj[-20:]


def amistoso(x):
    n = str((x.get("league") or {}).get("name") or "").lower()
    return "friendl" in n or "amistos" in n


def hist_jug(tid):
    jug = {}
    usados = 0
    eqsaves = []
    tname = ""
    cnt = {}
    lista = api("/fixtures", team=tid, last=HIST_MAX) or []
    lista = sorted(lista, key=lambda x: x["fixture"]["date"])
    for x in reversed(lista):
        if usados >= HIST_MAX:
            break
        if x["fixture"]["status"]["short"] not in ("FT", "AET", "PEN"):
            continue
        if amistoso(x):
            continue
        fid = x["fixture"]["id"]
        viejo = x["fixture"]["date"][:10] < CORTE
        d = jugadores_fixture(fid, viejo)
        mis = d.get(str(tid))
        if not mis:
            continue
        usados += 1
        es_h = x["teams"]["home"]["id"] == tid
        tname = x["teams"]["home" if es_h else "away"].get("name") or tname
        rival = x["teams"]["away" if es_h else "home"].get("name") or ""
        fecha = x["fixture"]["date"][:10]
        gk = [p for p in mis if p.get("pos") == "G"]
        if gk:
            eqsaves.append({
                "min": 90, "saves": sum(p["saves"] for p in gk),
                "local": es_h, "sub": False, "rv": rival, "fe": fecha})
        for p in mis:
            e = jug.setdefault(
                p["id"], {"n": p["n"], "pos": p["pos"], "g": []})
            e["g"].append(dict(p, local=es_h, rv=rival, fe=fecha))
            if calif(p):
                cnt[p["id"]] = cnt.get(p["id"], 0) + 1
        if sum(1 for v in cnt.values() if v >= 20) >= PARAR:
            break
    if eqsaves:
        jug[-tid] = {"n": "Porteros de " + tname, "pos": "G",
                     "g": eqsaves}
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


def inic(t, u):
    com = [w for w in t if len(w) >= 4 and w in u]
    if len(com) != 1:
        return False
    w = com[0]
    rt = list(t)
    ru = list(u)
    rt.remove(w)
    ru.remove(w)
    if not rt or not ru:
        return False
    if not all(len(x) == 1 for x in ru):
        return False
    letras = set(x[0] for x in rt)
    return any(x in letras for x in ru)


def buscar(nombre, jug):
    jug = {k: v for k, v in jug.items() if k >= 0}
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
        k = "".join(t[1:])
        if len(k) >= 4:
            c = [p for p, u in items if len(u) >= 2
                 and "".join(u[1:]) == k and compat(t[0], u[0])]
            if c:
                return unico(c)
        c = [p for p, u in items if len(u) >= 2
             and (inic(t, u) or inic(u, t))]
        if c:
            return unico(c)
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
    if len(t) == 1 and len(t[0]) >= 5:
        c = [p for p, u in items if len(u) >= 2 and u[0] == t[0]]
        if len(c) == 1:
            return c[0]
    return None


def prob_jug(juegos, stat, n, es_local):
    jj = validos(juegos, stat)
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
    jj = validos(juegos, stat)
    vacio = {"serie": [], "media": None, "minmed": None,
             "por90": None, "tit": None, "det": []}
    if not jj:
        return vacio
    vals = [g[stat] for g in jj]
    mins = sum(g["min"] for g in jj)
    por90 = None
    if mins > 0:
        por90 = round(sum(vals) * 90 / mins, 2)
    det = [{"r": g.get("rv") or "", "l": 1 if g.get("local") else 0,
            "m": g["min"]} for g in jj]
    return {
        "serie": list(reversed(vals))[:10],
        "media": round(sum(vals) / len(vals), 2),
        "minmed": round(mins / len(jj)),
        "por90": por90,
        "tit": None,
        "det": list(reversed(det))[:10],
    }
# fin
