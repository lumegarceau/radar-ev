import difflib
import json
import time
import unicodedata
import urllib.request
from datetime import datetime

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"
STAT = {
    "team_corners": "corners",
    "team_cards": "cards",
    "team_fouls": "fouls",
    "team_shots": "shots",
    "team_shots_on_target": "sot",
    "team_goals": "goals",
}
TOT = {
    "total_corners": "corners",
    "total_cards": "cards",
    "total_fouls": "fouls",
    "total_shots": "shots",
    "total_shots_on_target": "sot",
    "total_goals": "goals",
}
JUG = {
    "player_shots": "shots",
    "player_shots_on_target": "sot",
    "player_fouls_committed": "fouls",
    "player_fouls_drawn": "drawn",
    "player_saves": "saves",
    "player_tackles": "tk",
}
ALIAS = {
    "1xbet": "1XBET",
    "888sport": "888 Sports",
    "888sports": "888 Sports",
    "bet365": "Bet365",
    "betfair": "Betfair",
    "betsson": "Betsson",
    "betway": "Betway",
    "bwin": "Bwin",
    "grancasinomadrid": "Gran Casino Madrid",
    "casinogranmadrid": "Gran Casino Madrid",
    "casinomarbella": "Casino Marbella",
    "casumo": "Casumo",
    "codere": "Codere",
    "daznbet": "Daznbet",
    "enracha": "EnRacha",
    "goldenbull": "Goldenbull",
    "interwetten": "Interwetten",
    "kirolbet": "Kirolbet",
    "leovegas": "LeoVegas",
    "luckia": "Luckia",
    "marcaapuestas": "Marcaapuestas",
    "paf": "Paf",
    "retabet": "Retabet",
    "speedybet": "Speedybet",
    "sportium": "Sportium",
    "tonybet": "TonyBet",
    "versus": "Versus",
    "williamhill": "William Hill",
    "winamax": "Winamax",
    "yosports": "Yosports",
}
STOP = set([
    "fc", "cf", "club", "de", "del", "la", "el", "ac", "as", "sc", "afc",
    "cd", "ud", "sd", "fk", "sk", "ssc", "us", "calcio", "sv", "vfb", "vfl",
])
tipos = {}
saltadas = {}
omitidas = {"tarjetas": 0}


def vget(path):
    h = {"User-Agent": UA, "Accept": "application/json"}
    req = urllib.request.Request(BASE + path, headers=h)
    time.sleep(0.6)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return json.loads(r.read().decode("utf-8", "ignore"))
    except Exception as e:
        print("valueodds fallo", path[:60], str(e)[:60])
        return None


def listar(fecha):
    j = vget("/api/v1/fixtures?date=" + fecha)
    out = []

    def rec(o):
        if isinstance(o, dict):
            if "home_team" in o and "away_team" in o:
                out.append(o)
            for v in o.values():
                rec(v)
        elif isinstance(o, list):
            for v in o:
                rec(v)

    rec(j)
    return out


def idde(o):
    return o.get("sportmonks_id") or o.get("id")


def canon(n):
    k = "".join(c for c in n.lower() if c.isalnum())
    return ALIAS.get(k)


TRAD = {
    "turkey": "turkiye", "turquia": "turkiye",
    "czech republic": "czechia", "chequia": "czechia",
    "espana": "spain", "inglaterra": "england", "francia": "france",
    "italia": "italy", "alemania": "germany", "belgica": "belgium",
    "croacia": "croatia", "paises bajos": "netherlands",
    "holanda": "netherlands", "escocia": "scotland", "suiza": "switzerland",
    "grecia": "greece", "islandia": "iceland", "noruega": "norway",
    "dinamarca": "denmark", "polonia": "poland", "hungria": "hungary",
    "rumania": "romania", "irlanda": "ireland", "gales": "wales",
    "ucrania": "ukraine", "bosnia": "bosnia herzegovina",
    "eslovaquia": "slovakia", "eslovenia": "slovenia", "suecia": "sweden",
    "finlandia": "finland", "albania": "albania", "chipre": "cyprus",
    "armenia": "armenia", "bielorrusia": "belarus", "letonia": "latvia",
    "estonia": "estonia", "luxemburgo": "luxembourg", "bulgaria": "bulgaria",
    "azerbaiyan": "azerbaijan", "andorra": "andorra", "gibraltar": "gibraltar",
    "kazajistan": "kazakhstan", "moldavia": "moldova",
    "islas feroe": "faroe islands", "macedonia del norte": "north macedonia",
    "fyr macedonia": "north macedonia", "montenegro": "montenegro",
    "san marino": "san marino", "liechtenstein": "liechtenstein",
    "georgia": "georgia", "israel": "israel", "austria": "austria",
    "serbia": "serbia", "kosovo": "kosovo", "malta": "malta",
    "lituania": "lithuania", "irlanda del norte": "northern ireland",
    "r checa": "czechia", "republica checa": "czechia", "macedonia n": "north macedonia",
    "irlanda del n": "northern ireland", "macedonia del n": "north macedonia",
    "islas feroe": "faroe islands", "bosnia y herzegovina": "bosnia herzegovina",
}


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    r = " ".join(w for w in s.split() if w not in STOP)
    return TRAD.get(r, r)


def sim(a, b):
    a = norm(a)
    b = norm(b)
    if a and b and (a in b or b in a):
        return 0.9
    return difflib.SequenceMatcher(None, a, b).ratio()


def emparejar(loc, vis, dt, lista):
    mejor = None
    pm = 0
    for o in lista:
        s1 = sim(loc, o["home_team"].get("name", ""))
        s2 = sim(vis, o["away_team"].get("name", ""))
        if min(s1, s2) < 0.5:
            continue
        st = o.get("starts_at")
        if st:
            d2 = datetime.fromisoformat(st)
            if abs((d2 - dt).total_seconds()) > 10800:
                continue
        p = (s1 + s2) / 2
        if p > pm:
            mejor = o
            pm = p
    if pm >= 0.62:
        return mejor
    return None


def tarjetas_ok(m):
    seg = str(m.get("comparison_key", "")).split("|")
    extra = seg[5] if len(seg) > 5 else ""
    if not extra or "count" in extra:
        return True
    omitidas["tarjetas"] += 1
    return False


def cotizar(m, nombres, ahora):
    out = {}
    for s in m.get("selections") or []:
        code = s.get("code")
        if code not in ("over", "under"):
            continue
        for q in s.get("quotes") or []:
            nom = nombres.get(q[0], q[0])
            can = canon(nom)
            if not can:
                saltadas[nom] = saltadas.get(nom, 0) + 1
                continue
            if ahora - q[2] > 86400:
                continue
            try:
                c = float(q[1])
            except Exception:
                continue
            d = out.setdefault(code, {})
            if c > d.get(can, 0):
                d[can] = c
    return out


def acumular(dest, clave, q):
    d = dest.setdefault(clave, {})
    for casa, c in q.items():
        if c > d.get(casa, 0):
            d[casa] = c


def leer(j):
    nombres = {}
    for k, v in (j.get("bookmakers") or {}).items():
        nombres[k] = v.get("name", k)
    eq = {}
    tot = {}
    jug = {}
    ahora = time.time()
    for m in j.get("markets") or []:
        t = m.get("type")
        tipos[t] = tipos.get(t, 0) + 1
        if m.get("period") != "full_time" or m.get("settlement_label"):
            continue
        try:
            ln = float(m["line"])
        except Exception:
            continue
        if abs(ln % 1 - 0.5) > 0.001:
            continue
        pt = m.get("participant") or {}
        kind = pt.get("kind")
        if t in STAT and kind == "team":
            stat = STAT[t]
        elif t in TOT and kind == "none":
            stat = TOT[t]
        elif t in JUG and kind == "player":
            stat = JUG[t]
        else:
            continue
        if stat == "cards" and not tarjetas_ok(m):
            continue
        q = cotizar(m, nombres, ahora)
        for code, cu in q.items():
            if t in STAT:
                acumular(eq, (stat, pt.get("team_side"), ln, code), cu)
            elif t in TOT:
                acumular(tot, (stat, ln, code), cu)
            elif code == "over":
                nom = (pt.get("player") or {}).get("name")
                if nom:
                    acumular(jug, (stat, nom, ln), cu)
    return eq, tot, jug
