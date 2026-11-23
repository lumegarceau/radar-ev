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


# ---- Regla v1: probabilidad calibrada + anclaje al mercado -------------------
# El modelo v0 (rachas L20/L10/cond) sobreestimaba la probabilidad real (con 2000
# apuestas resueltas). v1 la corrige y la mezcla con lo que dice el mercado:
#   logit(p) = -0.24 + 0.33*logit(p_modelo) + 0.52*logit(1/cuota_mediana)
import math as _m


def _logit(p):
    p = min(max(p, 0.02), 0.98)
    return _m.log(p / (1 - p))


def calibrar(p_modelo, cuotas):
    """p_modelo: 0-1. cuotas: dict casa->cuota o lista de cuotas. Devuelve prob calibrada."""
    try:
        cs = sorted(float(c) for c in (cuotas.values() if hasattr(cuotas, "values") else cuotas) if c and float(c) > 1)
        if not cs:
            return p_modelo
        med = cs[len(cs) // 2] if len(cs) % 2 else (cs[len(cs) // 2 - 1] + cs[len(cs) // 2]) / 2
        z = -0.24 + 0.33 * _logit(p_modelo) + 0.52 * _logit(1 / med)
        return round(1 / (1 + _m.exp(-z)), 4)
    except Exception:
        return p_modelo
