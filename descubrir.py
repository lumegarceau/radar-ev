import json
import re
import time
import uuid

import socketio

SRV = "https://sports-eu-west-3.winamax.es"
URL = SRV + "?language=ES&version=3.72.1&embed=false"
PATH = "uof-sports-server/socket.io"
WEB = "https://www.winamax.es/apuestas-deportivas"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120",
    "Origin": "https://www.winamax.es",
    "Referer": WEB,
}
recibidos = []
sio = socketio.Client()


@sio.on("m")
def al_recibir(d):
    if isinstance(d, dict):
        recibidos.append(d)


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


def pedir(ruta, espera=12):
    recibidos.clear()
    msg = {"route": ruta}
    if not ruta.startswith("match"):
        msg["requestId"] = str(uuid.uuid4())
    sio.emit("m", msg)
    time.sleep(espera)
    datos = {}
    for m in list(recibidos):
        fusiona(m, datos)
    return datos


sio.connect(URL, socketio_path=PATH, transports=["websocket"],
            headers=H, wait_timeout=20)

print("A) TORNEOS DE FUTBOL")
d = pedir("sport:1", 10)
tor = d.get("tournaments", {})
print("   claves:", {k: len(v) for k, v in d.items()
                     if hasattr(v, "__len__")})
buscados = ["laliga", "segunda", "premier", "championship",
            "serie a", "ligue 1", "bundesliga", "eredivisie", "liga portugal"]
for k, v in tor.items():
    if not isinstance(v, dict):
        continue
    nom = str(v.get("title") or v.get("name"))
    if any(x in nom.lower() for x in buscados):
        print("  ", k, nom, "cat", v.get("categoryId"))
cats = d.get("categories", {})
for k, v in list(cats.items())[:5]:
    print("   cat", k, json.dumps(v, ensure_ascii=False)[:150])

print("")
print("B) PARTIDO DE LALIGA")
t = pedir("tournament:36")
ms = t.get("matches", {})
cand = [k for k, m in ms.items()
        if isinstance(m, dict) and m.get("period") == "not_started"]
mid = cand[0]
m = ms[mid]
print("   claves del partido:", sorted(m.keys()))
for k in sorted(m.keys()):
    if re.search(r"(?i)start|time|date|competitor|title", k):
        print("     ", k, "=", m[k])

d = pedir("match:" + str(mid), 15)
bets = d.get("bets", {})
outs = d.get("outcomes", {})
odds = d.get("odds", {})
lista = [b for b in bets.values() if isinstance(b, dict)]
print("   mercados:", len(lista))
print("")
print("C) JUGADORES (muestra)")
pl = d.get("players", {})
for k, v in list(pl.items())[:3]:
    print("  ", k, json.dumps(v, ensure_ascii=False)[:300])


def tit(b):
    return str(b.get("betTitle") or b.get("betTypeName") or "")


def crudo(b, n=5):
    base = {k: v for k, v in b.items() if k != "outcomes"}
    print("  BET", json.dumps(base, ensure_ascii=False)[:380])
    for o in (b.get("outcomes") or [])[:n]:
        x = json.dumps(outs.get(str(o)), ensure_ascii=False)
        print("     ", o, x[:260], "| cuota", odds.get(str(o)))


print("")
print("D) EJEMPLOS CRUDOS")
objetivos = [
    r"^Número de tiros por",
    r"^Número de tiros a puerta por",
    r"^Número exacto de córneres [A-Z]",
    r"^Realiza 2 o más remates$",
    r"^Realiza 2 o más remates a puerta$",
    r"^Comete 2 o más faltas$",
]
for pat in objetivos:
    hit = [b for b in lista if re.search(pat, tit(b))]
    print(" PATRON", pat, "->", len(hit))
    if hit:
        crudo(hit[0])

print("")
print("E) PARADAS, FALTAS RECIBIDAS, ENTRADAS")
pat = r"(?i)parad|portero|recibe|entrada|despej|fuera de juego"
for x in sorted(set(tit(b) for b in lista if re.search(pat, tit(b)))):
    print("   -", x)

print("")
print("F) TODOS LOS TITULOS")
tt = sorted(set(tit(b) for b in lista))
linea = ""
for x in tt:
    if len(linea) + len(x) > 850:
        print(linea)
        linea = ""
    linea += x + " ; "
print(linea)
sio.disconnect()
