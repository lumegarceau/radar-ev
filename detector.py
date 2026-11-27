"""Registro de errores de cuota en TODOS los mercados (no solo los del modelo).
Cada pasada de radar.py (equipos y totales) y props.py (jugadores) llama a
registrar() por cada linea con cuotas y al final a guardar().
Nunca debe romper el radar: todo va con try/except en quien lo llama."""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

MAD = ZoneInfo("Europe/Madrid")
ARCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "errores.json")
MIN_CASAS = 4
MIN_COMPARAR = 6
UMBRAL = 0.25
MIN_CUOTA = 1.40
MAX_SERIE = 80
GRUPOS = [
    {"paf", "leovegas", "casumo", "speedybet", "yosports", "enracha"},
    {"sportium", "marcaapuestas", "marca apuestas"},
    {"betfair", "pokerstars"},
]
PASADA = {}
CIERRE = {}


def grupo(nombre):
    n = str(nombre or "").strip().lower().replace("  ", " ")
    for i, g in enumerate(GRUPOS):
        if n in g:
            return "g%d" % i
    return n


def evaluar(q):
    """q = {casa: cuota}. Devuelve dict con el error o None.
    Caso 1: >= 4 casas independientes y la mejor supera en > 25 % a la segunda.
    Caso 2: >= 8 casas independientes y las dos mejores superan en > 25 %
    a la tercera."""
    por = {}
    for casa, c in (q or {}).items():
        try:
            c = float(c)
        except Exception:
            continue
        g = grupo(casa)
        if c > por.get(g, (0, ""))[0]:
            por[g] = (c, casa)
    orden = sorted(por.values(), key=lambda x: -x[0])
    n = len(orden)
    if n < MIN_CASAS or orden[0][0] < MIN_CUOTA:
        return None
    if orden[0][0] / orden[1][0] - 1 > UMBRAL:
        return {"casas": [orden[0][1]], "c": orden[0][0], "ref": orden[1][0],
                "n": n, "gap": round(orden[0][0] / orden[1][0] - 1, 3),
                "dos": False}
    if n >= 2 + MIN_COMPARAR and orden[1][0] / orden[2][0] - 1 > UMBRAL:
        return {"casas": [orden[0][1], orden[1][1]], "c": orden[0][0],
                "ref": orden[2][0], "n": n,
                "gap": round(orden[1][0] / orden[2][0] - 1, 3), "dos": True}
    return None


def ahora():
    return datetime.now(MAD).isoformat(timespec="minutes")


def _suficiente(h):
    """Al menos 10 partidos de referencia (el L10 solo cuenta partidos de titular)."""
    try:
        ps = [h.get("eq") or h.get("jug")] if (h.get("eq") or h.get("jug")) else [h.get("loc"), h.get("vis")]
        for p in ps:
            a, b = str((p or {}).get("l10", "")).split("/")
            if int(b) < 10:
                return False
        return True
    except Exception:
        return False


AUTO_EV_MIN = 0.0   # solo se publican los de EV positivo; si la cuota paga menos de lo que ocurre (EV < 0) se descarta


def _ok_error(x):
    """Mismo criterio que la pestaña de errores: cuota hasta 3,00 -> +30 %; mas de 3,00 -> +70 %."""
    if x["c"] > 5 and x["ref"] >= 2.5:
        return False
    return x["gap"] >= 0.30 if x["c"] <= 3 else x["gap"] >= 0.70


def _tasas(h):
    """(tasa L10, tasa L20, partidos L10) del historial; en totales el peor de los dos equipos."""
    ps = [h.get("eq") or h.get("jug")] if (h.get("eq") or h.get("jug")) else [h.get("loc"), h.get("vis")]
    t10, t20, n10 = [], [], []
    for p in ps:
        a, b = str(p["l10"]).split("/")
        c, e = str(p["l20"]).split("/")
        t10.append(int(a) / int(b))
        n10.append(int(b))
        t20.append(int(c) / int(e))
    return min(t10), min(t20), min(n10)


def _decidir(r, snap, t):
    """Seleccion automatica de un error de cuota. Se decide una vez, cuando el error
    cumple por primera vez el criterio, con la cuota y el historial de ese momento."""
    out = {"t": t, "c": snap["c"]}
    try:
        t10, t20, n10 = _tasas(r["hist"])
    except Exception:
        out.update({"ok": False, "m": "sin datos de referencia"})
        return out
    if n10 < 10:
        out.update({"ok": False, "m": "menos de 10 partidos de titular"})
        return out
    p = (t10 + t20) / 2
    ev = p * snap["c"] - 1
    out.update({"p": round(p, 3), "ev": round(ev, 3)})
    if ev < AUTO_EV_MIN:
        out.update({"ok": False, "m": "sin valor: paga menos de lo que ocurre"})
    else:
        out.update({"ok": True, "m": "valor"})
    return out


def registrar(clave, ctx, q):
    """clave unica de la linea; ctx = datos del partido y del suceso."""
    try:
        CIERRE[clave] = (ahora(), {b: float(c) for b, c in (q or {}).items()})
    except Exception:
        pass
    e = evaluar(q)
    if not e:
        return False
    h = (ctx or {}).get("hist")
    if h and not _suficiente(h):
        return False
    snap = dict(e)
    snap["t"] = ahora()
    snap["cuotas"] = [{"b": b, "c": c} for b, c in
                      sorted(q.items(), key=lambda kv: -kv[1])]
    PASADA[clave] = (dict(ctx), snap)
    return True


def guardar(tipos):
    """Mezcla lo visto en esta pasada con errores.json. Solo cierra los
    registros de los tipos indicados (cada script ve unos tipos)."""
    try:
        d = json.load(open(ARCH, encoding="utf-8"))
    except Exception:
        d = {}
    sel = d.get("sel") or {}
    t = ahora()
    nuevos = 0
    for clave, (ctx, snap) in PASADA.items():
        r = sel.get(clave)
        if r is None:
            r = dict(ctx)
            r.update({"estado": "pendiente", "primera": snap, "max": snap,
                      "vistas": 0, "serie": []})
            sel[clave] = r
            nuevos += 1
        r["ultima"] = snap
        if ctx.get("hist"):
            r["hist"] = ctx["hist"]
        r["vistas"] = r.get("vistas", 0) + 1
        r["activo"] = True
        r["aus"] = 0
        r["cerrado"] = None
        if snap["gap"] > r["max"]["gap"]:
            r["max"] = snap
        r["serie"].append({"t": t, "c": snap["c"], "ref": snap["ref"],
                           "gap": snap["gap"], "b": snap["casas"]})
        r["serie"] = r["serie"][-MAX_SERIE:]
        if "auto" not in r and _ok_error(snap):
            r["auto"] = _decidir(r, snap, t)
    # Criterio nuevo (EV >= 0): se reevaluan los ya publicados de partidos sin empezar.
    # Los de partidos ya jugados no se tocan.
    try:
        _ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        for r in sel.values():
            a = r.get("auto")
            if (a and a.get("ok") and a.get("ev") is not None and a["ev"] < AUTO_EV_MIN
                    and datetime.fromisoformat(r["inicio"]) > _ahora):
                a["ok"] = False
                a["m"] = "sin valor: paga menos de lo que ocurre"
    except Exception as e:
        print("detector: reevaluacion fallo", repr(e)[:80])
    cerrados = 0
    try:
        from rcommon import agotado as _agotado
        sin_api = len(PASADA) == 0 and _agotado()
    except Exception:
        sin_api = False
    if sin_api:
        print("errores de cuota: la API no ha dado datos (limite diario); no se cierran por ausencia")
    for clave, r in sel.items():
        if not r.get("activo"):
            continue
        if clave in PASADA:
            continue
        ini = str(r.get("inicio") or "")
        if ini and ini <= t:
            r["activo"] = False
            r["cerrado"] = ini
            cerrados += 1
            continue
        if r.get("tipo") in tipos and not sin_api:
            r["aus"] = r.get("aus", 0) + 1
            if r["aus"] >= 2:
                r["activo"] = False
                r["cerrado"] = t
                cerrados += 1
    # cuota de cierre (para el CLV): ultima cuota vista antes del partido, aunque
    # la casa ya haya corregido el error. No toca primera / max / ultima.
    try:
        for clave, (t0, q0) in CIERRE.items():
            r = sel.get(clave)
            if not r or r.get("estado") != "pendiente" or not q0:
                continue
            ini = str(r.get("inicio") or "")
            if ini and ini <= t:
                continue
            gs = {grupo(b) for b in ((r.get("primera") or {}).get("casas") or [])}
            otras = [c for b, c in q0.items() if grupo(b) not in gs]
            r["cierre"] = {"t": t0, "c": max(q0.values()),
                           "ref": max(otras) if otras else None,
                           "cuotas": [{"b": b, "c": c} for b, c in
                                      sorted(q0.items(), key=lambda kv: -kv[1])[:8]]}
    except Exception as ex:
        print("cuota de cierre: fallo controlado", repr(ex)[:100])
    d = {"v": 1, "actualizado": t, "sel": sel}
    json.dump(d, open(ARCH, "w", encoding="utf-8"), ensure_ascii=False)
    print("errores de cuota (todos los mercados): vistos", len(PASADA),
          "| nuevos", nuevos, "| cerrados", cerrados,
          "| en registro", len(sel))
    PASADA.clear()
    CIERRE.clear()
