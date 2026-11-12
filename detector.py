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


def registrar(clave, ctx, q):
    """clave unica de la linea; ctx = datos del partido y del suceso."""
    e = evaluar(q)
    if not e:
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
        r["vistas"] = r.get("vistas", 0) + 1
        r["activo"] = True
        r["aus"] = 0
        r["cerrado"] = None
        if snap["gap"] > r["max"]["gap"]:
            r["max"] = snap
        r["serie"].append({"t": t, "c": snap["c"], "ref": snap["ref"],
                           "gap": snap["gap"], "b": snap["casas"]})
        r["serie"] = r["serie"][-MAX_SERIE:]
    cerrados = 0
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
        if r.get("tipo") in tipos:
            r["aus"] = r.get("aus", 0) + 1
            if r["aus"] >= 2:
                r["activo"] = False
                r["cerrado"] = t
                cerrados += 1
    d = {"v": 1, "actualizado": t, "sel": sel}
    json.dump(d, open(ARCH, "w", encoding="utf-8"), ensure_ascii=False)
    print("errores de cuota (todos los mercados): vistos", len(PASADA),
          "| nuevos", nuevos, "| cerrados", cerrados,
          "| en registro", len(sel))
    PASADA.clear()
