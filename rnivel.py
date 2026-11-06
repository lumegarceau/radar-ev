import atexit
import json
import os
import re
import unicodedata
from rcommon import api

# Nivel de cada pais (1 = el mas fuerte). Los que no estan aqui son nivel 3.
# Solo se usa cuando no hay Elo de alguno de los dos equipos.
NIVEL = {
    "England": 1, "Spain": 1, "Italy": 1, "Germany": 1, "France": 1,
    "Portugal": 2, "Netherlands": 2, "Belgium": 2, "Turkey": 2,
    "Scotland": 2, "Austria": 2, "Czech-Republic": 2, "Greece": 2,
    "Switzerland": 2, "Norway": 2, "Denmark": 2, "Poland": 2,
    "Croatia": 2, "Serbia": 2, "Ukraine": 2, "Sweden": 2,
}
CODIGO = {
    "England": "ENG", "Spain": "ESP", "Italy": "ITA", "Germany": "GER",
    "France": "FRA", "Portugal": "POR", "Netherlands": "NED",
    "Belgium": "BEL", "Turkey": "TUR", "Scotland": "SCO", "Austria": "AUT",
    "Czech-Republic": "CZE", "Greece": "GRE", "Switzerland": "SUI",
    "Norway": "NOR", "Denmark": "DEN", "Poland": "POL", "Croatia": "CRO",
    "Serbia": "SRB", "Ukraine": "UKR", "Sweden": "SWE", "Russia": "RUS",
    "Hungary": "HUN", "Cyprus": "CYP", "Israel": "ISR", "Bulgaria": "BUL",
    "Romania": "ROU", "Slovakia": "SVK", "Slovenia": "SVN",
    "Azerbaijan": "AZE", "Kazakhstan": "KAZ", "Finland": "FIN",
    "Ireland": "IRL", "Northern-Ireland": "NIR", "Wales": "WAL",
    "Iceland": "ISL", "Latvia": "LVA", "Lithuania": "LTU",
    "Estonia": "EST", "Georgia": "GEO", "Armenia": "ARM",
    "Belarus": "BLR", "Bosnia-and-Herzegovina": "BIH", "Albania": "ALB",
    "North-Macedonia": "MKD", "Montenegro": "MNE", "Kosovo": "KOS",
    "Luxembourg": "LUX", "Malta": "MLT", "Moldova": "MDA",
}
# Nombre en API-Football -> nombre en la lista de Elo (ambos sin tildes)
ALIAS = {
    "manchester city": "man city", "manchester united": "man united",
    "paris saint germain": "paris sg", "bayern munich": "bayern munchen",
    "borussia dortmund": "dortmund", "bayer leverkusen": "leverkusen",
    "borussia monchengladbach": "gladbach",
    "eintracht frankfurt": "frankfurt", "inter": "internazionale",
    "ac milan": "milan", "as roma": "roma", "real betis": "betis",
    "atletico madrid": "atletico", "sporting cp": "sporting",
    "fc porto": "porto", "club brugge kv": "brugge",
    "union st gilloise": "st gillis", "red bull salzburg": "rb salzburg",
    "psv eindhoven": "psv", "nottingham forest": "forest",
    "wolverhampton wanderers": "wolves", "celta vigo": "celta",
    "deportivo la coruna": "depor", "lech poznan": "lech",
    "fc copenhagen": "fc kobenhavn", "shakhtar donetsk": "shakhtar",
    "olympiacos": "olympiakos", "ferencvarosi tc": "ferencvaros",
    "red star belgrade": "crvena zvezda", "sk slavia praha": "slavia praha",
    "sparta prague": "sparta praha", "slavia prague": "slavia praha",
    "rb leipzig": "rb leipzig", "1 fsv mainz 05": "mainz",
    "fc koln": "koln", "fc augsburg": "augsburg", "sc freiburg": "freiburg",
    "tsg hoffenheim": "hoffenheim", "vfb stuttgart": "stuttgart",
    "werder bremen": "werder", "hamburger sv": "hamburg",
    "rayo vallecano": "rayo vallecano", "real sociedad": "real sociedad",
    "athletic club": "athletic club", "olympique lyonnais": "lyon",
    "olympique marseille": "marseille", "as monaco": "monaco",
    "ogc nice": "nice", "stade rennais": "rennes",
    "1899 hoffenheim": "hoffenheim", "az alkmaar": "az",
    "fsv mainz 05": "mainz", "sc paderborn 07": "paderborn",
    "sv elversberg": "elversberg", "racing santander": "santander",
}
ATAQUE = ("corners", "shots", "sot", "goals")
UMBRAL = 100
SUELO = 1643
ARCHIVO = "elo.txt"
bloqueadas = [0]
st = {"elo_ok": 0, "elo_bloq": 0, "pais_bloq": 0, "sin_elo": set()}
_elo = {}
_cargado = [False]
_memo = {}


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(s.split())


def cargar():
    if _cargado[0]:
        return
    _cargado[0] = True
    if not os.path.exists(ARCHIVO):
        return
    for ln in open(ARCHIVO, encoding="utf-8"):
        ln = ln.replace("\t", "  ").strip()
        m = re.match(r"^([A-Z]{3})\s+\d+\s+(.+?)\s{1,}(\d{3,4})(?:\s|$)", ln)
        if m:
            _elo.setdefault(m.group(1), []).append(
                (norm(m.group(2)), float(m.group(3))))


def info(tid):
    f = "cache/c" + str(tid) + ".json"
    d = {}
    if os.path.exists(f):
        try:
            d = json.load(open(f))
        except Exception:
            d = {}
    if d.get("p") and d.get("n"):
        return d.get("n"), d.get("p")
    r = api("/teams", id=tid)
    if not r:
        return d.get("n"), d.get("p")
    t = r[0].get("team") or {}
    d = {"p": t.get("country") or d.get("p"), "n": t.get("name")}
    if d["p"]:
        json.dump(d, open(f, "w"))
    return d.get("n"), d.get("p")


def pais(tid):
    return info(tid)[1]


def nivel(tid):
    p = pais(tid)
    if not p:
        return None
    return NIVEL.get(p, 3)


def sim(a, b):
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio()


def elo(tid):
    if tid in _memo:
        return _memo[tid]
    cargar()
    res = None
    if _elo:
        n, p = info(tid)
        nn = norm(n)
        nn = ALIAS.get(nn, nn)
        cod = CODIGO.get(p)
        cands = _elo.get(cod, []) if cod else [
            x for v in _elo.values() for x in v]
        for nom, e in cands:
            if nom == nn:
                res = e
                break
        if res is None and cands:
            pun = sorted(((sim(nn, nom), e) for nom, e in cands),
                         reverse=True)
            if pun and pun[0][0] >= 0.88 and (
                    len(pun) == 1 or pun[0][0] - pun[1][0] >= 0.06):
                res = pun[0][1]
        if res is None:
            st["sin_elo"].add(str(n))
    _memo[tid] = res
    return res


def por_elo(a, b, sent):
    """True/False si Elo decide; None si no se puede decidir."""
    ea = elo(a)
    eb = elo(b)
    if ea is None and eb is None:
        return None
    if ea is not None and eb is not None:
        st["elo_ok"] += 1
        d = eb - ea
        if sent == "over":
            return d >= UMBRAL
        return -d >= UMBRAL
    if sent == "over":
        if ea is None:
            return (eb - SUELO) >= UMBRAL or None
        return None
    if eb is None:
        return (ea - SUELO) >= UMBRAL or None
    return None


def bloquea(tid, rival, stat, sent):
    if stat not in ATAQUE:
        return False
    r = por_elo(tid, rival, sent)
    if r is True:
        bloqueadas[0] += 1
        st["elo_bloq"] += 1
        return True
    if r is False:
        return False
    a = nivel(tid)
    b = nivel(rival)
    if a is None or b is None:
        return False
    if (a > b and sent == "over") or (a < b and sent == "under"):
        bloqueadas[0] += 1
        st["pais_bloq"] += 1
        return True
    return False


def resumen():
    cargar()
    n = sum(len(v) for v in _elo.values())
    print("nivel: clubes en elo.txt:", n, "| decididos por Elo:",
          st["elo_ok"], "| bloqueos por Elo:", st["elo_bloq"],
          "| bloqueos por pais:", st["pais_bloq"])
    if st["sin_elo"]:
        print("nivel: equipos sin Elo:", sorted(st["sin_elo"])[:40])


atexit.register(resumen)
# fin
