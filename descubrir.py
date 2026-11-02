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
FAM = {
    "corners": r"(?i)c[oó]rner|esquina",
    "tarjetas": r"(?i)tarjeta|amarill",
    "faltas": r"(?i)falta",
    "tiros": r"(?i)tiro|remate|disparo",
    "entradas": r"(?i)entrada|tackle",
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
    if ruta.startswith("tournament"):
        msg["requestId"] = str(uuid.uuid4())
    sio.emit("m", msg)
    time.sleep(espera)
    datos = {}
    for m in list(recibidos):
        fusiona(m, datos)
    print("   mensajes:", len(recibidos))
    res = {}
    for k, v in datos.items():
        if hasattr(v, "__len__"):
            res[k] = len(v)
    print("   claves:", res)
    return datos


def titulo(b):
    for k in ("betTitle", "title", "betTypeName", "betType", "name"):
        v = b.get(k)
        if isinstance(v, str) and v:
            return v
    return ""


def texto(b):
    t = titulo(b)
    if t:
        return t
    s = json.dumps(b, ensure_ascii=False)
    return s.replace("skillcorner", "")


sio.connect(URL, socketio_path=PATH, transports=["websocket"],
            headers=H, wait_timeout=20)
print("A) LALIGA (torneo 36)")
t = pedir("tournament:36")
ms = t.get("matches", {})
cand = []
for mid, m in ms.items():
    if isinstance(m, dict) and m.get("period") == "not_started":
        cand.append(mid)
if not cand:
    cand = list(ms.keys())
print("   partidos:", len(cand))
for mid in cand[:3]:
    print("  ", mid, json.dumps(ms[mid], ensure_ascii=False)[:450])
if not cand:
    sio.disconnect()
    raise SystemExit

mid = cand[0]
print("")
print("B) PARTIDO", mid)
d = pedir("match:" + str(mid), 15)
bets = d.get("bets", {})
outs = d.get("outcomes", {})
odds = d.get("odds", {})
lista = [b for b in bets.values() if isinstance(b, dict)]
print("   mercados:", len(lista), "selecciones:", len(outs),
      "cuotas:", len(odds))
if lista:
    print("   claves:", sorted(lista[0].keys()))
    print("   ejemplo:", json.dumps(lista[0], ensure_ascii=False)[:600])


def mostrar(b):
    print("  ", titulo(b), "|", b.get("specialBetValue"),
          "|", b.get("marketId"))
    for o in (b.get("outcomes") or [])[:6]:
        x = outs.get(str(o), {})
        print("      ", x.get("label"), odds.get(str(o)), x.get("code"))


print("")
print("C) FAMILIAS DE MERCADOS")
for fam, pat in FAM.items():
    hit = [b for b in lista if re.search(pat, texto(b))]
    tit = sorted(set(titulo(b) for b in hit))
    print(" ", fam, ":", len(hit), "mercados")
    for x in tit[:10]:
        print("     -", x)
    if hit:
        print("   ejemplo de", fam)
        mostrar(hit[0])
        if len(hit) > 3:
            mostrar(hit[3])

print("")
print("D) TODOS LOS TITULOS")
tt = sorted(set(titulo(b) for b in lista))
print("  ", len(tt), "titulos distintos")
for x in tt[:70]:
    print("   -", x)
sio.disconnect()
