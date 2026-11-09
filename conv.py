import json
import os
from datetime import date
import rjug

ARCH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "convocatorias.json")
ALIAS = {
    "turkey": "turkiye", "turquia": "turkiye",
    "czech republic": "czechia", "chequia": "czechia",
    "espana": "spain", "inglaterra": "england", "francia": "france",
    "italia": "italy", "alemania": "germany", "belgica": "belgium",
}
_d = {}


def _cargar():
    if "x" not in _d:
        try:
            _d["x"] = json.load(open(ARCH, encoding="utf-8"))
        except Exception:
            _d["x"] = {}
    return _d["x"]


def clave(nombre):
    n = rjug.norm(nombre)
    return ALIAS.get(n, n)


def vigente(hoy=None):
    d = _cargar()
    try:
        lim = date.fromisoformat(d.get("valido_hasta", "2000-01-01"))
    except Exception:
        return False
    return (hoy or date.today()) <= lim


def pids(equipo, jug, hoy=None):
    """Ids de jugadores convocados que aparecen en el historial del equipo.
    Si no hay lista vigente para esa seleccion devuelve conjunto vacio."""
    if not vigente(hoy):
        return set()
    lista = (_cargar().get("equipos") or {}).get(clave(equipo))
    if not lista:
        return set()
    out = set()
    for nom in lista:
        p = rjug.buscar(nom, jug)
        if p is not None:
            out.add(p)
    return out
