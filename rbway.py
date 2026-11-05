import json
import os
import re
import time
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

MAD = ZoneInfo("Europe/Madrid")
ARCHIVO = "betway.json"
STAT_EQ = {
    "Córners": "corners",
    "Tarjetas": "cards",
    "Faltas": "fouls",
    "Tiros A Puerta": "sot",
    "Tiros": "shots",
}
TIT_JUG = {
    "Entradas": "tk",
    "Faltas": "fouls",
    "Faltas Cometidas": "fouls",
    "Faltas Recibidas": "drawn",
}
TIROS = "Tiros"
OTROS_TIT = set([
    "Goleador", "Fuera de juego", "Asiste 1+ Goles",
    "Tarjetas", "Tiros A Puerta Especiales", "Tiros A Puerta Cada Uno",
    "Tiros A Puerta Uno Contra Uno", "Goleadores Combinados",
])
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado",
        "domingo"]
RE_TIT = re.compile(
    r"^(?:(.+?) )?(Córners|Tarjetas|Faltas|Tiros A Puerta|Tiros) En Total$")
RE_OU = re.compile(r"^([OU]) (\d+(?:\.\d+)?)$")
RE_ODD = re.compile(r"^\d+,\d+$")


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(s.split())


def lado_de(nombre, c1, c2):
    n = norm(nombre)
    a = norm(c1)
    b = norm(c2)
    if not n:
        return None
    ya = n in a or (a != "" and a in n)
    yb = n in b or (b != "" and b in n)
    if ya and not yb:
        return "home"
    if yb and not ya:
        return "away"
    return None


def lineas(texto):
    out = []
    for x in str(texto).split("\n"):
        x = x.strip()
        if x:
            out.append(x)
    return out


def cuota(x):
    return float(x.replace(",", "."))


def medio(ln):
    return abs(ln % 1 - 0.5) < 0.001


def parsear_mercados(lns, c1, c2):
    equipo = []
    total = []
    n = len(lns)
    for i in range(n):
        m = RE_TIT.match(lns[i])
        if not m:
            continue
        pref = m.group(1)
        stat = STAT_EQ[m.group(2)]
        lado = None
        if pref:
            lado = lado_de(pref, c1, c2)
            if lado is None:
                continue
        j = i + 1
        while j < n:
            x = lns[j]
            o = RE_OU.match(x)
            if o and j + 1 < n and RE_ODD.match(lns[j + 1]):
                ln = float(o.group(2))
                c = cuota(lns[j + 1])
                s = "over" if o.group(1) == "O" else "under"
                if medio(ln) and not (stat == "cards" and ln > 15):
                    if lado is None:
                        total.append((stat, ln, c, s))
                    else:
                        equipo.append((stat, lado, ln, c, s))
                j += 2
            elif x in ("Tiempo completo", "1er Tiempo", "Más de",
                       "Menos de"):
                j += 1
            else:
                break
    return equipo, total


def parsear_jugadores(lns, stat_tiros):
    out = []
    estado = None
    heads = []
    nombre = None
    idx = 0
    for x in lns:
        if x == TIROS:
            estado = stat_tiros
            heads = []
            nombre = None
            continue
        if x == "Paradas del portero":
            estado = "saves_eq"
            heads = []
            nombre = None
            continue
        if x in TIT_JUG:
            estado = TIT_JUG[x]
            heads = []
            nombre = None
            continue
        if x in OTROS_TIT:
            estado = None
            heads = []
            nombre = None
            continue
        if estado is None:
            continue
        if re.match(r"^\d+\+$", x) and nombre is None:
            heads.append(int(x[:-1]))
            continue
        if not heads:
            continue
        if x.startswith("Ver todas"):
            nombre = None
            continue
        if RE_ODD.match(x):
            if nombre and idx < len(heads):
                out.append((estado, nombre, heads[idx], cuota(x)))
            idx += 1
            continue
        if x == "—":
            idx += 1
            continue
        nombre = x
        idx = 0
    return out


def inicio(lns, c1, now=None):
    now = now or datetime.now(MAD)
    for i, x in enumerate(lns):
        if re.match(r"^\d{2}:\d{2}$", x) and i + 1 < len(lns):
            dia = lns[i + 1].lower()
            hh, mm = int(x[:2]), int(x[3:])
            base = now.date()
            if dia == "hoy":
                d = base
            elif dia == "mañana":
                d = base + timedelta(days=1)
            elif dia in DIAS:
                k = (DIAS.index(dia) - base.weekday()) % 7
                d = base + timedelta(days=k)
            else:
                return None
            t = datetime(d.year, d.month, d.day, hh, mm, tzinfo=MAD)
            return t.timestamp()
    return None


def cargar(max_horas=10):
    try:
        d = json.load(open(ARCHIVO))
    except Exception:
        return []
    if time.time() - d.get("ts", 0) > max_horas * 3600:
        print("betway.json antiguo: no se usa")
        return []
    return d.get("partidos", [])


def anadir(cu, w):
    for stat, lado, ln, c, s in w["equipo"]:
        d = cu.setdefault(("eq", stat, lado, ln, s), {})
        if c > d.get("Betway", 0):
            d["Betway"] = c
    for stat, ln, c, s in w["total"]:
        d = cu.setdefault(("tot", stat, "total", ln, s), {})
        if c > d.get("Betway", 0):
            d["Betway"] = c
