import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

KEY = os.environ.get("ODDSPAPI_KEY", "")
BASE = "https://api.oddspapi.io/v4"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
usadas = [0]


def api(path, **p):
    p["apiKey"] = KEY
    url = BASE + "/" + path + "?" + urllib.parse.urlencode(p)
    for i in range(3):
        usadas[0] += 1
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            r = urllib.request.urlopen(req, timeout=180)
            return json.loads(r.read().decode("utf-8", "ignore"))
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "ignore")
            if e.code == 429:
                print("429, espero:", txt[:120])
                time.sleep(3)
                continue
            print("HTTP", e.code, path, txt[:250])
            return None
        except Exception as e:
            print("fallo", path, str(e)[:80])
            return None
    return None


def items(j):
    if isinstance(j, dict) and isinstance(j.get("data"), (list, dict)):
        j = j["data"]
    out = []
    if isinstance(j, dict):
        for k, v in j.items():
            out.append((str(k), v if isinstance(v, dict) else {}))
    elif isinstance(j, list):
        for v in j:
            if isinstance(v, dict):
                s = v.get("slug") or v.get("bookmaker") or v.get("name") or ""
                out.append((str(s), v))
    return out


def nk(s):
    return "".join(c for c in str(s).lower() if c.isalnum())


QUIERO = {
    "1xBet": "1xbet", "888 Sports": "888", "Bet365": "bet365",
    "Betfair": "betfair", "Betsson": "betsson", "Betway": "betway",
    "Bwin": "bwin", "Gran Casino Madrid": "madrid",
    "Casino Marbella": "marbella", "Codere": "codere", "Daznbet": "dazn",
    "Goldenbull": "golden", "Interwetten": "interwetten",
    "Kirolbet": "kirol", "Luckia": "luckia", "Marcaapuestas": "marca",
    "Paf": "paf", "Retabet": "reta", "Speedybet": "speedy",
    "Sportium": "sportium", "Versus": "versus",
    "William Hill": "williamhill", "Winamax": "winamax",
    "Yosports": "yosports",
}
FAM = ["corner", "card", "booking", "foul", "shot", "tackle"]

print("1) CASAS EN OddsPapi")
cs = items(api("bookmakers"))
print("Entradas:", len(cs))
if cs:
    print("Ejemplo:", cs[0][0], json.dumps(cs[0][1], ensure_ascii=False)[:250])
slugs = [s for s, v in cs]
for nom, tok in QUIERO.items():
    m = [s for s in slugs if tok in nk(s)]
    print(" ", nom, "->", ", ".join(m[:6]) if m else "NO ENCONTRADA")

print("")
print("2) PARTIDO DE PRUEBA")
hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
rango = {"from": str(hoy), "to": str(hoy + timedelta(days=3))}
fid = None
for tid in (8, 17, 23, 35, 34):
    j = api("fixtures", sportId=10, tournamentId=tid, **rango)
    fx = items(j) if j else []
    print("  torneo", tid, "->", len(fx), "partidos")
    if fx:
        f = fx[0][1]
        print("  claves:", list(f.keys())[:20])
        print("  ejemplo:", json.dumps(f, ensure_ascii=False)[:300])
        fid = f.get("fixtureId") or f.get("id")
        if fid:
            break
if not fid:
    print("Sin partido de prueba")
    raise SystemExit
print("  usando fixture", fid)

od = api("odds", fixtureId=fid)
bo = (od or {}).get("bookmakerOdds") or {}
print("Casas con cuotas en este partido:", len(bo))
mk = items(api("markets"))
nombres = {}
for k, v in mk:
    idv = v.get("marketId") or v.get("id") or k
    nm = v.get("marketName") or v.get("name") or v.get("market") or ""
    nombres[str(idv)] = str(nm)
print("Mercados en catalogo:", len(nombres))
if mk:
    print("Ejemplo mercado:", json.dumps(mk[0][1], ensure_ascii=False)[:200])

mias = {}
for nom, tok in QUIERO.items():
    for s in bo:
        if tok in nk(s):
            mias.setdefault(nom, []).append(s)
print("")
print("3) MERCADOS POR CASA (este partido)")
for nom, ss in mias.items():
    for s in ss:
        mer = (bo[s] or {}).get("markets") or {}
        cuenta = {}
        for mid in mer:
            n = nombres.get(str(mid), "").lower()
            for fam in FAM:
                if fam in n:
                    cuenta[fam] = cu
