import json
import os
from rcommon import api

# Nivel de cada pais (1 = el mas fuerte). Los que no estan aqui son nivel 3.
# Puedes editar esta lista cuando quieras.
NIVEL = {
    "England": 1, "Spain": 1, "Italy": 1, "Germany": 1, "France": 1,
    "Portugal": 2, "Netherlands": 2, "Belgium": 2, "Turkey": 2,
    "Scotland": 2, "Austria": 2, "Czech-Republic": 2, "Greece": 2,
    "Switzerland": 2, "Norway": 2, "Denmark": 2, "Poland": 2,
    "Croatia": 2, "Serbia": 2, "Ukraine": 2, "Sweden": 2,
}
ATAQUE = ("corners", "shots", "sot", "goals")
bloqueadas = [0]


def pais(tid):
    f = "cache/c" + str(tid) + ".json"
    if os.path.exists(f):
        try:
            return json.load(open(f)).get("p")
        except Exception:
            pass
    r = api("/teams", id=tid)
    if not r:
        return None
    p = (r[0].get("team") or {}).get("country")
    if p:
        json.dump({"p": p}, open(f, "w"))
    return p


def nivel(tid):
    p = pais(tid)
    if not p:
        return None
    return NIVEL.get(p, 3)


def bloquea(tid, rival, stat, sent):
    if stat not in ATAQUE:
        return False
    a = nivel(tid)
    b = nivel(rival)
    if a is None or b is None:
        return False
    if (a > b and sent == "over") or (a < b and sent == "under"):
        bloqueadas[0] += 1
        return True
    return False
