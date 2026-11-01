import json, os, sys, time
import urllib.parse, urllib.request

KEY = os.environ.get("API_FOOTBALL_KEY", "")
BASE = "https://v3.football.api-sports.io"
PAUSA = float(os.environ.get("PAUSA", "0.3"))
gasto = [0]
os.makedirs("cache", exist_ok=True)


def api(ruta, **p):
    q = urllib.parse.urlencode(p)
    hd = {"x-apisports-key": KEY}
    req = urllib.request.Request(BASE + ruta + "?" + q, headers=hd)
    for i in range(3):
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
            if "rateLimit" in str(err):
                time.sleep(30)
                continue
            return None
        return j["response"]
    return None
