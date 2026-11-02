import difflib
import json
import time
import unicodedata
import urllib.request
from datetime import datetime

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"
MERC = {
    "team_corners": "corners",
    "team_cards": "cards",
    "team_fouls": "fouls",
    "team_shots": "shots",
    "team_shots_on_target": "sot",
    "team_goals": "goals",
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


def norm(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(w for w in s.split() if w not in STOP)


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


def leer_cuotas(j):
    nombres = {}
    for k, v in (j.get("bookmakers") or {}).items():
        nombres[k] = v.get("name", k)
    out = {}
    ahora = time.time()
    for m in j.get("markets") or []:
        t = m.get("type")
        tipos[t] = tipos.get(t, 0) + 1
        if t not in MERC or m.get("period") != "full_time":
            continue
        if m.get("settlement_label"):
            continue
        pt = m.get("participant") or {}
        if pt.get("kind") != "team":
            continue
        try:
            ln = float(m["line"])
        except Exception:
            continue
        for s in m.get("selections") or []:
            if s.get("code") != "over":
                continue
            for q in s.get("quotes") or []:
                nom = nombres.get(q[0], q[0])
                can = canon(nom)
                if not can:
                    saltadas[nom] = saltadas.get(nom, 0) + 1
                    continue
                if ahora - q[2] > 86400:
                    continue
                c = float(q[1])
                d = out.setdefault((t, pt.get("team_side"), ln), {})
                if c > d.get(can, 0):
                    d[can] = c
    return out
