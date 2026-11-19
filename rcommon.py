import json
import os
import sys
import time
import urllib.parse
import urllib.request

KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
PAUSA = float(os.environ.get("PAUSA", "0.15"))
LIMITE = int(os.environ.get("LIMITE", "6800"))
RESERVA = int(os.environ.get("RESERVA", "200"))  # peticiones del dia que se dejan sin gastar
TIEMPO = int(os.environ.get("TIEMPO", "2700"))
t0 = time.time()
gasto = [0]
os.makedirs("cache", exist_ok=True)


def agotado():
    if gasto[0] >= LIMITE:
        return True
    return time.time() - t0 > TIEMPO


def api(ruta, **p):
    q = urllib.parse.urlencode(p)
    hd = {"x-apisports-key": KEY}
    req = urllib.request.Request(BASE + ruta + "?" + q, headers=hd)
    for i in range(3):
        if agotado():
            return None
        time.sleep(PAUSA)
        gasto[0] += 1
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            quedan = resp.headers.get("x-ratelimit-requests-remaining")
            j = json.load(resp)
        except Exception as e:
            print("fallo conexion", ruta, str(e)[:60])
            time.sleep(5)
            continue
        err = j.get("errors")
        if err:
            print("error API", ruta, err)
            if isinstance(err, dict) and "requests" in err:
                gasto[0] = LIMITE
                return None
            if "rateLimit" in str(err):
                time.sleep(30)
                continue
            return None
        if quedan and str(quedan).isdigit() and int(quedan) < RESERVA:
            print("API-Football: quedan", quedan, "peticiones hoy; se para para no agotarlas")
            gasto[0] = LIMITE
        return j["response"]
    return None
