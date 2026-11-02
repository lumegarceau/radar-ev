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


def titulares(fid, tid):
    f = "cache/l" + str(fid) + ".json"
    d = None
    if os.path.exists(f):
        d = json.load(open(f))
    else:
        r = api("/fixtures/lineups", fixture=fid)
        if r:
            d = {}
            for t in r:
                xi = t.get("startXI") or []
                d[str(t["team"]["id"])] = [
                    p["player"]["id"] for p in xi]
            if len(d) == 2:
                json.dump(d, open(f, "w"))
    if not d:
        return None
    return d.get(str(tid))


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
    if r["estado"] != "pendiente":
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
    for k in ks:
        r = sel[k]
        sent = r.get("sentido") or "over"
        lin = r["linea"]
        if r["tipo"] == "jugador":
            tid = th if r["condTxt"] == "local" else ta
            lista = pj.get(str(tid)) or []
            jug = {p["id"]: {"n": p["n"]} for p in lista}
            pre = " " + str(lin) + "+ "
            nombre = r["suceso"].rsplit(pre, 1)[0]
            pid = rjug.buscar(nombre, jug)
            if pid is None:
                r["estado"] = "revisar"
                r["motivo"] = "jugador no encontrado"
                continue
            xi = titulares(fid, tid)
            if xi is None:
                continue
            if pid not in xi:
                r["estado"] = "nula"
                r["motivo"] = "no titular"
                continue
            p = [y for y in lista if y["id"] == pid][0]
            v = p.get(r["mercado"])
            if v is None:
                continue
            gana = v >= lin
        else:
            v = valor(r, fx, st, th, ta)
            if v is None:
                continue
            gana = (v < lin) if sent == "under" else (v > lin)
        r["valor"] = v
        r["estado"] = "ganada" if gana else "perdida"
        r["resuelta"] = ahora.isoformat(timespec="minutes")
json.dump(H, open(FH, "w"), ensure_ascii=False)
cuenta = {}
for r in sel.values():
    cuenta[r["estado"]] = cuenta.get(r["estado"], 0) + 1
print("estados:", cuenta)
print("peticiones API-Football:", gasto[0])
