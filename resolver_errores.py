"""Resuelve los errores de cuota de errores.json cuando el partido ha acabado.
No toca historial.json. Si algo falla, no rompe nada."""
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rcommon import api, gasto
import rmodelo
import rjug
from resultados_comun import alineacion

MAD = ZoneInfo("Europe/Madrid")
ARCH = "errores.json"
NULAS = ("PST", "CANC", "ABD", "AWD", "WO")
FIN = ("FT", "AET", "PEN")


def valor_equipo(r, key, fx, st, th, ta):
    m = r["mercado"]
    if r["tipo"] == "total":
        if m == "goals":
            a, b = fx["goals"]["home"], fx["goals"]["away"]
            return None if a is None or b is None else a + b
        va = (st.get(str(th)) or {}).get(m)
        vb = (st.get(str(ta)) or {}).get(m)
        return None if va is None or vb is None else va + vb
    lado = key.split("|")[3]
    if m == "goals":
        return fx["goals"][lado]
    return (st.get(str(th if lado == "home" else ta)) or {}).get(m)


def main():
    try:
        d = json.load(open(ARCH, encoding="utf-8"))
    except Exception:
        print("resolver errores: todavia no hay errores.json")
        return
    sel = d.get("sel") or {}
    ahora = datetime.now(MAD)
    pend = {}
    for k, r in sel.items():
        if r.get("estado") != "pendiente":
            continue
        ini = datetime.fromisoformat(r["inicio"])
        if ahora > ini + timedelta(hours=72):
            r["estado"] = "revisar"
            r["motivo"] = "sin datos tras 3 dias"
            continue
        if ahora < ini + timedelta(hours=3):
            continue
        pend.setdefault(r["fixture"], []).append(k)
    print("errores de cuota: partidos por resolver:", len(pend))
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
            lin = r["linea"]
            if r["tipo"] == "jugador":
                pid = int(k.split("|")[3])
                es_h = r.get("equipo") == fx["teams"]["home"]["name"]
                tid = th if es_h else ta
                lista = pj.get(str(tid)) or []
                if not lista:
                    continue
                if pid < 0:
                    v = sum(p.get(r["mercado"]) or 0 for p in lista)
                    r["valor"] = v
                    r["estado"] = "ganada" if v >= lin else "perdida"
                    r["resuelta"] = ahora.isoformat(timespec="minutes")
                    continue
                p0 = [y for y in lista if y["id"] == pid]
                if not p0:
                    r["estado"] = "nula"
                    r["motivo"] = "no convocado"
                    continue
                if al is not None:
                    xi = al["xi"].get(str(tid)) or []
                    if pid not in xi:
                        r["estado"] = "nula"
                        r["motivo"] = "suplente"
                        continue
                else:
                    sub = p0[0].get("sub")
                    if sub is None:
                        continue
                    if sub:
                        r["estado"] = "nula"
                        r["motivo"] = "suplente"
                        continue
                v = p0[0].get(r["mercado"])
                if v is None:
                    continue
                gana = v >= lin
            else:
                v = valor_equipo(r, k, fx, st, th, ta)
                if v is None:
                    continue
                gana = (v < lin) if r.get("sentido") == "under" else (v > lin)
            r["valor"] = v
            r.pop("motivo", None)
            r["estado"] = "ganada" if gana else "perdida"
            r["resuelta"] = ahora.isoformat(timespec="minutes")
    json.dump(d, open(ARCH, "w", encoding="utf-8"), ensure_ascii=False)
    c = {}
    for r in sel.values():
        c[r["estado"]] = c.get(r["estado"], 0) + 1
    print("errores de cuota: estados", c, "| peticiones API-Football:", gasto[0])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("resolver errores: fallo controlado:", repr(e)[:200])
