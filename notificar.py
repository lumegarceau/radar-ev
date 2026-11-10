"""Avisa por Telegram (solo al propietario) cuando aparece un posible error de
cuota nuevo (ver evaluar() para las dos reglas)."""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT = os.environ.get("TELEGRAM_CHAT", "")
ARCHIVO = "notificados.json"
MIN_CASAS = 4
MIN_COMPARAR = 6
UMBRAL = 0.25
# casas que comparten cuotas: cuentan como una sola
GRUPOS = [
    {"paf", "leovegas", "casumo", "speedybet", "yosports", "enracha"},
    {"sportium", "marcaapuestas", "marca apuestas"},
]


def grupo(nombre):
    n = str(nombre or "").strip().lower().replace("  ", " ")
    for i, g in enumerate(GRUPOS):
        if n in g:
            return "g%d" % i
    return n


def evaluar(sel):
    """Devuelve un dict con el aviso o None.
    Caso 1: >= 4 casas independientes y la mejor supera en > 25 % a la segunda.
    Caso 2: dos casas por encima y >= 6 casas independientes con las que
    comparar: las dos superan en > 25 % a la tercera mejor."""
    por = {}
    for o in sel.get("cuotas") or []:
        try:
            c = float(o["c"])
        except Exception:
            continue
        g = grupo(o.get("b"))
        if c > por.get(g, (0, ""))[0]:
            por[g] = (c, o.get("b"))
    orden = sorted(por.values(), key=lambda x: -x[0])
    n = len(orden)
    if n >= MIN_CASAS and orden[0][0] / orden[1][0] - 1 > UMBRAL:
        return {"casas": [orden[0][1]], "mejor": orden[0][0], "ref": orden[1][0],
                "n": n, "gap": orden[0][0] / orden[1][0] - 1, "dos": False}
    if n >= 2 + MIN_COMPARAR:
        ref = orden[2][0]
        if orden[1][0] / ref - 1 > UMBRAL:
            return {"casas": [orden[0][1], orden[1][1]], "mejor": orden[0][0],
                    "ref": ref, "n": n, "gap": orden[1][0] / ref - 1, "dos": True,
                    "segunda": orden[1][0]}
    return None


def enviar(texto):
    if not TOKEN or not CHAT:
        print("sin TELEGRAM_TOKEN/TELEGRAM_CHAT: no se envia")
        return False
    url = "https://api.telegram.org/bot%s/sendMessage" % TOKEN
    datos = urllib.parse.urlencode({"chat_id": CHAT, "text": texto}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(url, data=datos), timeout=30)
        return True
    except Exception as e:
        print("telegram falla:", str(e)[:100])
        return False


def main():
    try:
        sel = json.load(open("historial.json", encoding="utf-8")).get("sel", {})
    except Exception as e:
        print("sin historial:", e)
        return
    try:
        hechos = json.load(open(ARCHIVO, encoding="utf-8"))
    except Exception:
        hechos = {}
    ahora = time.time()
    nuevos = 0
    for k, r in sel.items():
        if r.get("vigente") is False:
            continue
        try:
            ini = datetime.fromisoformat(r["inicio"]).timestamp()
        except Exception:
            continue
        if ini <= ahora:
            continue
        ev = evaluar(r)
        if not ev:
            continue
        clave = "%s|%s|%s" % (r.get("fixture"), r.get("suceso"), "+".join(sorted(ev["casas"])))
        if clave in hechos:
            continue
        cab = "Posible error de cuota en DOS casas" if ev["dos"] else "Posible error de cuota"
        if ev["dos"]:
            det = ("%s a %.2f y %s a %.2f; el resto de casas, como mucho %.2f (+%d %% la menor de las dos) "
                   "· %d casas independientes"
                   % (ev["casas"][0], ev["mejor"], ev["casas"][1], ev["segunda"], ev["ref"],
                      round(ev["gap"] * 100), ev["n"]))
        else:
            det = ("%s a %.2f, la siguiente casa %.2f (+%d %%) · %d casas independientes"
                   % (ev["casas"][0], ev["mejor"], ev["ref"], round(ev["gap"] * 100), ev["n"]))
        texto = "%s\n%s v %s · %s\n%s\n%s" % (cab, r.get("local"), r.get("visitante"),
                                              r.get("hora", ""), r.get("suceso"), det)
        print(texto.replace("\n", " | "))
        if enviar(texto) or not TOKEN:
            hechos[clave] = ahora
            nuevos += 1
    # limpiar avisos de hace mas de 5 dias
    hechos = {k: v for k, v in hechos.items() if ahora - v < 5 * 86400}
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(hechos, f)
    print("avisos nuevos:", nuevos)


if __name__ == "__main__":
    main()
