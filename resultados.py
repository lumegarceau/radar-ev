import difflib
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rcommon import api, gasto
import rmodelo
import rjug

MAD = ZoneInfo("Europe/Madrid")
FH = "historial.json"
NULAS = ("PST", "CANC", "ABD", "AWD", "WO")
FIN = ("FT", "AET", "PEN")
REV = ("jugador no encontrado", "sin datos del jugador", "sin alineacion")


def alineacion(fid):
    f = "cache/L" + str(fid) + ".json"
    if os.path.exists(f):
        return json.load(open(f))
    r = api("/fixtures/lineups", fixture=fid)
    if not r:
        return None
    d = {"xi": {}, "sub": {}, "n": {}}
    for t in r:
        tid = str(t["team"]["id"])
        xi = t.get("startXI") or []
        sb = t.get("substitutes") or []
        d["xi"][tid] = [p["player"]["id"] for p in xi]
        d["sub"][tid] = [p["player"]["id"] for p in sb]
        for p in xi + sb:
            d["n"][str(p["player"]["id"])] = p["player"]["name"]
    ok = len(d["xi"]) == 2 and all(d["xi"].values())
    if not ok:
        return None
    json.dump(d, open(f, "w"))
    return d


def sin_parecido(nombre, nombres):
    t = set(x for x in rjug.norm(nombre).split() if len(x) >= 3)
    if not t:
        return False
    for n in nombres:
        u = set(rjug.norm(n).split())
        if t & u:
            return False
        for a in t:
            for b in u:
                if len(a) >= 5 and len(b) >= 5:
                    r = difflib.SequenceMatcher(None, a, b).ratio()
                    if r >= 0.8:
                        return False
    return True


def valor(r, fx, st, th, ta):
    m = r["mercado"]
    if r["tipo"] == "total":
        if m == "goals":
            a = fx["goals"]["home"]
            b = fx["goals"]["away"]
            if a is None or b is None:
                return None
            return a + b
        va = (st.get(str(th)) or {}).get(m)
        vb = (st.get(str(ta)) or {}).get(m)
        if va is None or vb is None:
            return None
        return va + vb
    es_h = r["condTxt"] == "local"
    if m == "goals":
        return fx["goals"]["home" if es_h else "away"]
    tid = th if es_h else ta
    return (st.get(str(tid)) or {}).get(m)


try:
    H = json.load(open(FH))
except Exception:
    print("todavia no hay historial.json")
    raise SystemExit
sel = H["sel"]
ahora = datetime.now(MAD)
pend = {}
for k, r in sel.items():
    rev = r["estado"] == "revisar" and r.get("motivo") in REV
    if r["estado"] != "pendiente" and not rev:
        continue
    ini = datetime.fromisoformat(r["inicio"])
    if ahora > ini + timedelta(hours=72):
        r["estado"] = "revisar"
        r["motivo"] = "sin datos tras 3 dias"
        continue
    if ahora < ini + timedelta(hours=3):
        continue
    pend.setdefault(r["fixture"], []).append(k)
print("partidos por corregir:", len(pend))
for fid, ks in pend.items():
    fx = api("/fixtures", id=fid)
    if not fx:
        continue
    fx = fx[0]
    est = fx["fixture"]["status"]["short"]
    th = fx["teams"]["home"]["id"]
    ta = fx["teams"]["away"]["id"]
    if est in NULAS:
        for k in ks:
            sel[k]["estado"] = "nula"
            sel[k]["motivo"] = "partido " + est
        continue
    if est not in FIN:
        continue
    hay_e = any(sel[k]["tipo"] != "jugador" for k in ks)
    hay_j = any(sel[k]["tipo"] == "jugador" for k in ks)
    st = rmodelo.stats(fid, True) if hay_e else {}
    pj = rjug.jugadores_fixture(fid, True) if hay_j else {}
    al = alineacion(fid) if hay_j else None
    for k in ks:
        r = sel[k]
        sent = r.get("sentido") or "over"
        lin = r["linea"]
        if r["tipo"] == "jugador":
            es_h = r["condTxt"] == "local"
            tid = th if es_h else ta
            lista = pj.get(str(tid)) or []
            xi = []
            sb = []
            nombres = [p["n"] for p in lista]
            if al is not None:
                xi = al["xi"].get(str(tid)) or []
                sb = al["sub"].get(str(tid)) or []
                nombres += [al["n"].get(str(i), "") for i in xi + sb]
            if not nombres:
                continue
            pid = r.get("pid")
            pre = " " + str(lin) + "+ "
            nombre = r["suceso"].rsplit(pre, 1)[0]
            if pid is None:
                jug = {}
                for p in lista:
                    jug[p["id"]] = {"n": p["n"]}
                for i in xi + sb:
                    jug[i] = {"n": al["n"].get(str(i), "")}
                pid = rjug.buscar(nombre, jug)
            if pid is None:
                if sin_parecido(nombre, nombres):
                    r["estado"] = "nula"
                    r["motivo"] = "no convocado"
                else:
                    r["estado"] = "revisar"
                    r["motivo"] = "jugador no encontrado"
                continue
            p0 = [y for y in lista if y["id"] == pid]
            if al is not None:
                if pid not in xi:
                    r["estado"] = "nula"
                    r["motivo"] = "suplente" if pid in sb else "no convocado"
                    continue
            else:
                if not p0:
                    r["estado"] = "nula"
                    r["motivo"] = "no convocado"
                    continue
                sub = p0[0].get("sub")
                if sub is None:
                    r["estado"] = "revisar"
                    r["motivo"] = "sin alineacion"
                    continue
                if sub:
                    r["estado"] = "nula"
                    r["motivo"] = "suplente"
                    continue
            if not p0:
                r["estado"] = "revisar"
                r["motivo"] = "sin datos del jugador"
                continue
            v = p0[0].get(r["mercado"])
            if v is None:
                continue
            gana = v >= lin
        else:
            v = valor(r, fx, st, th, ta)
            if v is None:
                continue
            gana = (v < lin) if sent == "under" else (v > lin)
        r["valor"] = v
        r.pop("motivo", None)
        r["estado"] = "ganada" if gana else "perdida"
        r["resuelta"] = ahora.isoformat(timespec="minutes")
json.dump(H, open(FH, "w"), ensure_ascii=False)
cuenta = {}
for r in sel.values():
    cuenta[r["estado"]] = cuenta.get(r["estado"], 0) + 1
print("estados:", cuenta)
for r in sel.values():
    if r["estado"] == "revisar":
        print("A REVISAR:", r["suceso"], "|", r["local"], "v",
              r["visitante"], "|", r.get("motivo"))
print("peticiones API-Football:", gasto[0])
