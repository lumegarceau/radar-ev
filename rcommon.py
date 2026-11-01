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
            j = json.load(urllib.request.urlopen(req, timeout=30))
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
        return j["response"]
    return None
