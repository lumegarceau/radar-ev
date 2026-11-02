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


def valor_equipo(r, fx, st, tid):
    m = r["mercado"]
    if m == "goals":
        lado = "home" if r["condTxt"] == "local" else "away"
        return fx["goals"][lado]
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
    h = fx["teams"]["home"]["id"]
    a = fx["teams"]["away"]["id"]
    if est in NULAS:
        for k in ks:
            sel[k]["estado"] = "nula"
            sel[k]["motivo"] = "partido " + est
        continue
    if est not in FIN:
        continue
    st = rmodelo.stats(fid, True)
    hay_j = any(sel[k]["tipo"] == "jugador" for k in ks)
    pj = {}
    if hay_j:
        pj = rjug.jugadores_fixture(fid, True)
    for k in ks:
        r = sel[k]
        es_h = r["condTxt"] == "local"
        tid = h if es_h else a
        lin = r["linea"]
        if r["tipo"] == "jugador":
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
            p = [x for x in lista if x["id"] == pid][0]
            v = p.get(r["mercado"])
            gana = v is not None and v >= lin
        else:
            v = valor_equipo(r, fx, st, tid)
            if v is None:
                continue
            gana = v > lin
        r["valor"] = v
        r["estado"] = "ganada" if gana else "perdida"
        r["resuelta"] = ahora.isoformat(timespec="minutes")
json.dump(H, open(FH, "w"), ensure_ascii=False)
cuenta = {}
for r in sel.values():
    cuenta[r["estado"]] = cuenta.get(r["estado"], 0) + 1
print("estados:", cuenta)
print("peticiones API-Football:", gasto[0])
