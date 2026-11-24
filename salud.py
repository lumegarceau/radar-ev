"""Vigilancia del sistema: avisa por Telegram (y deja salud.json para la app) cuando algo va mal.
Se ejecuta en cada pasada del radar. Solo avisa cuando aparece un problema nuevo, cuando se
resuelve y, mientras siga sin resolverse, un recordatorio al dia."""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT = os.environ.get("TELEGRAM_CHAT", "")
ARCH = "salud.json"
AHORA = time.time()

# (archivo, nombre, edad maxima en horas, pasadas seguidas con 0 partidos antes de avisar)
FUENTES = [
    ("sportium", "Sportium", 14, 3),
    ("marca", "Marca Apuestas", 14, 3),
    ("betsson", "Betsson", 14, 3),
    ("betway", "Betway", 14, 3),
    # juegging.json: en pausa desde 24/11 (Akamai bloquea con 403), no se vigila
    ("eldorado", "Eldorado", 30, 3),
    ("betfair", "Betfair", 20, 3),
]
RADAR_MAX_H = 10
REPETIR_H = 24


def leer(f):
    try:
        return json.load(open(f))
    except Exception:
        return None


def enviar(texto):
    if not TOKEN or not CHAT:
        print("salud: sin TELEGRAM_TOKEN/TELEGRAM_CHAT, no se envia:\n" + texto)
        return
    datos = urllib.parse.urlencode({"chat_id": CHAT, "text": texto}).encode()
    try:
        urllib.request.urlopen(urllib.request.Request(
            "https://api.telegram.org/bot" + TOKEN + "/sendMessage", data=datos), timeout=30)
    except Exception as e:
        print("salud: fallo al enviar", repr(e)[:80])


def edad_iso(s):
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(s)).total_seconds() / 3600
    except Exception:
        return None


def main():
    est = leer(ARCH) or {}
    prev = est.get("estado", {})
    nuevo = {}
    problemas = {}   # clave -> texto

    for f, nom, max_h, max_ceros in FUENTES:
        d = leer(f + ".json")
        st = prev.get(f, {"ceros": 0, "max": 0})
        if not d or not isinstance(d.get("partidos"), list):
            problemas[f] = nom + ": el archivo de cuotas no se puede leer."
            nuevo[f] = st
            continue
        n = len(d["partidos"])
        h = (AHORA - d["ts"]) / 3600 if d.get("ts") else None
        if n == 0:
            st["ceros"] = st.get("ceros", 0) + 1
        else:
            st["ceros"] = 0
            st["max"] = max(n, int(st.get("max", 0) * 0.9))
        nuevo[f] = st
        if h is not None and h > max_h:
            problemas[f] = "%s: sin actualizarse desde hace %d h." % (nom, h)
        elif st["ceros"] >= max_ceros:
            problemas[f] = "%s: 0 partidos en las ultimas %d pasadas." % (nom, st["ceros"])
        elif st["max"] >= 8 and n < st["max"] * 0.25:
            problemas[f] = "%s: solo %d partidos (lo normal ronda %d)." % (nom, n, st["max"])

    r = leer("radar-data.json") or {}
    h = edad_iso(r.get("updated_at", "")) if r.get("updated_at") else None
    if h is None:
        # updated_at viene con zona horaria; si no se puede leer, no se vigila
        pass
    elif h > RADAR_MAX_H:
        problemas["radar"] = "Radar: sin recalcular desde hace %d h." % h
    elif r.get("props_ok") is False:
        problemas["props"] = "Props de jugador: la ultima pasada no ha leido cuotas de Winamax."
    nc = sum(len(dia.get("candidatos", [])) for dia in r.get("days", []))
    if r.get("updated_at") and nc == 0:
        problemas["vacio"] = "Radar: la ultima pasada no ha dejado ninguna apuesta candidata."

    avisados = est.get("avisados", {})
    nuevos, repetir, resueltos = [], [], []
    for k, t in problemas.items():
        ult = avisados.get(k)
        if ult is None:
            nuevos.append(t)
            avisados[k] = AHORA
        elif (AHORA - ult) / 3600 >= REPETIR_H:
            repetir.append(t)
            avisados[k] = AHORA
    for k in list(avisados):
        if k not in problemas:
            resueltos.append(k)
            del avisados[k]

    msg = []
    if nuevos:
        msg.append("⚠ EV RADAR — problemas nuevos:\n- " + "\n- ".join(nuevos))
    if repetir:
        msg.append("⚠ Siguen sin resolverse:\n- " + "\n- ".join(repetir))
    if resueltos:
        msg.append("✅ Resuelto: " + ", ".join(resueltos))
    if msg:
        enviar("\n\n".join(msg))

    json.dump({"ts": AHORA, "problemas": sorted(problemas.values()),
               "estado": nuevo, "avisados": avisados},
              open(ARCH, "w"), ensure_ascii=False, indent=1)
    print("salud:", len(problemas), "problemas |", "; ".join(problemas.values()) or "todo en orden")


try:
    main()
except Exception as e:
    print("salud: fallo", repr(e)[:200])
