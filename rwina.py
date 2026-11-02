import re
import time
import unicodedata
import uuid

import socketio

SRV = "https://sports-eu-west-3.winamax.es"
URL = SRV + "?language=ES&version=3.72.1&embed=false"
PATH = "uof-sports-server/socket.io"
WEB = "https://www.winamax.es/apuestas-deportivas"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"
H = {"User-Agent": UA, "Origin": "https://www.winamax.es", "Referer": WEB}
EQUIPO = [
    ("shots", r"^Número de tiros por (.+)$"),
    ("sot", r"^Número de tiros a puerta por (.+)$"),
    ("corners", r"^Número total córneres (.+)$"),
    ("fouls", r"^Número de faltas cometidas por (.+)$"),
    ("goals", r"^Número total de goles marcados por (.+)$"),
]
TOTAL = [
    ("corners", r"^Número total córneres$"),
    ("fouls", r"^Número de faltas cometidas$"),
    ("shots", r"^Número de tiros$"),
    ("sot", r"^Número de tiros a puerta$"),
    ("goals", r"^Número total de goles$"),
]
JUGADOR = [
    ("shots", r"^Realiza (\d+) o más remates$"),
    ("sot", r"^Realiza (\d+) o más remates a puerta$"),
    ("fouls", r"^Comete (\d+) o más faltas$"),
    ("drawn", r"^Recibe (\d+) o más faltas$"),
    ("saves", r"^Realiza (\d+) o más paradas$"),
]
recibidos = []
estado = {"sio": None}


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


def numero(v):
    m = re.search(r"-?\d+(?:\.\d+)?", str(v or ""))
    if m:
        return float(m.group())
    return None


def medio(ln):
    return ln is not None and abs(ln % 1 - 0.5) < 0.001


def sentido(label):
    s = str(label or "")
    if s.startswith("Más de"):
        return "over"
    if s.startswith("Menos de"):
        return "under"
    return None


def ok_sel(x, b):
    if x.get("available") is False:
        return False
    bx = x.get("betId")
    return bx is None or bx == b.get("betId")


def fusiona(m, datos):
    for k, v in m.items():
        if not isinstance(v, dict):
            datos[k] = v
            continue
        dest = datos.setdefault(k, {})
        for i, x in v.items():
            old = dest.get(i)
            if isinstance(x, dict) and isinstance(old, dict):
                old.update(x)
            else:
                dest[i] = x


def cerrar():
    s = estado["sio"]
    if s is not None:
        try:
            s.disconnect()
        except Exception:
            pass
    estado["sio"] = None


def conectar():
    cerrar()
    sio = socketio.Client(reconnection=False)

    @sio.on("m")
    def al_recibir(d):
        if isinstance(d, dict):
            recibidos.append(d)

    sio.connect(URL, socketio_path=PATH, transports=["websocket"],
                headers=H, wait_timeout=20)
    estado["sio"] = sio


def pedir(ruta, clave, maximo=25):
    recibidos.clear()
    msg = {"route": ruta}
    if not ruta.startswith("match"):
        msg["requestId"] = str(uuid.uuid4())
    estado["sio"].emit("m", msg)
    t0 = time.time()
    visto = 0
    ultimo = None
    while time.time() - t0 < maximo:
        time.sleep(0.5)
        n = len(recibidos)
        if n != visto:
            visto = n
            ultimo = time.time()
        tiene = any(clave in m for m in list(recibidos))
        if tiene and ultimo and time.time() - ultimo > 2.5:
            break
    datos = {}
    for m in list(recibidos):
        fusiona(m, datos)
    return datos


def sube(v):
    v = sorted(v)
    for i in range(1, len(v)):
        if v[i][1] < v[i - 1][1] - 0.0001:
            return False
    return True


def baja(v):
    v = sorted(v)
    for i in range(1, len(v)):
        if v[i][1] > v[i - 1][1] + 0.0001:
            return False
    return True


def limpiar(res):
    desc = 0
    g = {}
    for t in res["equipo"]:
        g.setdefault((t[0], t[1], t[4]), []).append(t)
    malos = set()
    for k, v in g.items():
        pares = [(x[2], x[3]) for x in v]
        ok = sube(pares) if k[2] == "over" else baja(pares)
        if not ok:
            malos.add(k)
    res["equipo"] = [t for t in res["equipo"]
                     if (t[0], t[1], t[4]) not in malos]
    desc += len(malos)
    g = {}
    for t in res["total"]:
        g.setdefault((t[0], t[3]), []).append(t)
    malos = set()
    for k, v in g.items():
        pares = [(x[1], x[2]) for x in v]
        ok = sube(pares) if k[1] == "over" else baja(pares)
        if not ok:
            malos.add(k)
    res["total"] = [t for t in res["total"] if (t[0], t[3]) not in malos]
    desc += len(malos)
    g = {}
    for t in res["jugador"]:
        g.setdefault((t[0], t[1]), []).append(t)
    malos = set()
    for k, v in g.items():
        if not sube([(x[4], x[5]) for x in v]):
            malos.add(k)
    res["jugador"] = [t for t in res["jugador"]
                      if (t[0], t[1]) not in malos]
    desc += len(malos)
    res["descartes"] = desc
    return res


def parsear(mid, meta, d):
    bets = d.get("bets", {})
    outs = d.get("outcomes", {})
    odds = d.get("odds", {})
    c1 = meta.get("competitor1Name", "")
    c2 = meta.get("competitor2Name", "")
    res = {
        "id": mid, "c1": c1, "c2": c2,
        "inicio": meta.get("matchStart"),
        "equipo": [], "total": [], "jugador": [],
    }
    for b in bets.values():
        if not isinstance(b, dict):
            continue
        if b.get("available") is False:
            continue
        if str(b.get("matchId")) != str(mid):
            continue
        t = str(b.get("betTitle") or "").strip()
        ln = numero(b.get("specialBetValue"))
        for stat, pat in EQUIPO:
            m = re.match(pat, t)
            if not m:
                continue
            lado = lado_de(m.group(1), c1, c2)
            if lado is None or not medio(ln):
                continue
            for o in b.get("outcomes") or []:
                x = outs.get(str(o)) or {}
                s = sentido(x.get("label"))
                c = odds.get(str(o))
                if s is None or not c or not ok_sel(x, b):
                    continue
                res["equipo"].append((stat, lado, ln, float(c), s))
        for stat, pat in TOTAL:
            if not re.match(pat, t) or not medio(ln):
                continue
            for o in b.get("outcomes") or []:
                x = outs.get(str(o)) or {}
                s = sentido(x.get("label"))
                c = odds.get(str(o))
                if s is None or not c or not ok_sel(x, b):
                    continue
                res["total"].append((stat, ln, float(c), s))
        for stat, pat in JUGADOR:
            m = re.match(pat, t)
            if not m:
                continue
            n = int(m.group(1))
            for o in b.get("outcomes") or []:
                x = outs.get(str(o)) or {}
                c = odds.get(str(o))
                if not c or not ok_sel(x, b):
                    continue
                lado = "away"
                if x.get("team") == 1:
                    lado = "home"
                nom = str(x.get("label", "")).strip()
                sr = x.get("srPlayerId")
                res["jugador"].append((stat, nom, sr, lado, n, float(c)))
    return limpiar(res)


def partidos(srids, desde, hasta):
    conectar()
    d = pedir("sport:1", "matches", 40)
    ms = d.get("matches", {})
    sin = [m for m in ms.values()
           if isinstance(m, dict) and "srTournamentId" not in m]
    print("winamax: partidos en total", len(ms), "sin torneo", len(sin))
    sel = []
    for mid, m in ms.items():
        if not isinstance(m, dict):
            continue
        if m.get("srTournamentId") not in srids:
            continue
        ini = m.get("matchStart") or 0
        if ini < desde or ini > hasta:
            continue
        if m.get("status") != "PREMATCH":
            continue
        sel.append((mid, m))
    print("winamax: partidos de mis ligas", len(sel))
    out = []
    desc = 0
    for i, (mid, m) in enumerate(sel):
        try:
            if i and i % 12 == 0:
                conectar()
            dd = pedir("match:" + str(mid), "bets", 25)
        except Exception as e:
            print("winamax fallo", mid, repr(e)[:80])
            try:
                conectar()
            except Exception:
                break
            continue
        meta = (dd.get("matches") or {}).get(str(mid)) or m
        r = parsear(mid, meta, dd)
        desc += r.get("descartes", 0)
        out.append(r)
    cerrar()
    print("winamax: descartes por cuotas incoherentes:", desc)
    return out
