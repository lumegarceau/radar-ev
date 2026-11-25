"""Sonda 2 Betinia/Altenar: partidos MAS PROXIMOS: solo peticiones HTTP a traves del proxy espanol.
Busca ligas, partidos y mercados de jugador."""
import json
import os
import re
from datetime import datetime, timezone
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://sb2frontend-altenar2.biahosted.com/api/"
Q = {"culture": "es-ES", "timezoneOffset": "-60", "integration": "betiniaes", "deviceType": "1",
     "numFormat": "en-GB", "countryCode": "ES"}
PAL = re.compile(r"jugador|player|tiros?|remates?|shots?|faltas?|fouls?|tarjetas?|cards?|entradas?|tackles?|fuera de juego|offsides?", re.I)
raw = "".join(os.environ.get("PROXY_URL", "").split())
if raw and "://" not in raw:
    raw = "http://" + raw
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": raw, "https": raw}))
TOTAL = [0]


def get(ruta, **extra):
    url = BASE + ruta + "?" + urllib.parse.urlencode(dict(Q, **extra))
    rq = urllib.request.Request(url, headers={"User-Agent": UA, "Origin": "https://betinia.es", "Referer": "https://betinia.es/"})
    try:
        b = OP.open(rq, timeout=40).read()
        TOTAL[0] += len(b)
        return json.loads(b)
    except Exception as e:
        print("  falla", ruta, extra, repr(e)[:120])
        return None


def buscar_champs(o, out):
    if isinstance(o, dict):
        if "name" in o and "id" in o and ("sportId" in o or "catId" in o or "eventsCount" in o or "ec" in o):
            out.append(o)
        for v in o.values():
            buscar_champs(v, out)
    elif isinstance(o, list):
        for v in o:
            buscar_champs(v, out)


CHAMPS = {16808: "Champions", 16809: "Europa League", 2941: "LaLiga", 2936: "Premier", 2942: "Serie A", 2950: "Bundesliga", 2943: "Ligue 1"}
AHORA = datetime.now(timezone.utc)
evs = []
for cid, n in CHAMPS.items():
    j = get("widget/GetEvents", champIds=cid, sportId=66) or get("widget/GetUpcoming", champIds=cid, sportId=66, eventCount=20) or {}
    for e in j.get("events") or []:
        try:
            ini = datetime.fromisoformat(e["startDate"].replace("Z", "+00:00"))
        except Exception:
            continue
        if ini > AHORA:
            evs.append((ini, n, e))
evs.sort(key=lambda x: x[0])
print("partidos futuros encontrados:", len(evs))
for ini, n, e in evs[:8]:
    print("  ", ini.strftime("%d/%m %H:%M UTC"), n, "|", e.get("name"), "| id", e.get("id"))

JUG = re.compile(r"tiros?|remates?|faltas?|fuera de juego|entradas?|tarjeta|paradas?|shots?|fouls?", re.I)
for ini, n, e in evs[:3]:
    print("\n== DETALLE", e.get("name"), ini.strftime("%d/%m %H:%M UTC"))
    d = get("widget/GetEventDetails", eventId=e.get("id"))
    if not d:
        continue
    mk = d.get("markets") or []
    nombres = []
    for m in mk:
        nm = str(m.get("name"))
        if nm not in nombres:
            nombres.append(nm)
    print("mercados:", len(mk), "| nombres distintos:", len(nombres))
    jug = [x for x in nombres if JUG.search(x)]
    print("con tiros/faltas/entradas/tarjeta/paradas/fuera de juego:", len(jug))
    for x in jug[:40]:
        print("   -", x)
    ch = {c.get("id"): c for c in (d.get("childMarkets") or [])}
    odds = {o.get("id"): o for o in (d.get("odds") or [])}
    for m in mk:
        if JUG.search(str(m.get("name"))) and m.get("childMarketIds"):
            c = ch.get(m["childMarketIds"][0]) or {}
            print("   ESTRUCTURA de", m.get("name"), "| hijos:", len(m["childMarketIds"]))
            print("     padre claves:", sorted(m.keys())[:14])
            print("     hijo:", json.dumps({k: v for k, v in c.items() if k != "desktopOddIds"}, ensure_ascii=False)[:420])
            ids = c.get("desktopOddIds") or c.get("mobileOddIds") or []
            print("     cuotas del hijo:", json.dumps([odds.get(i) for i in ids[:3]], ensure_ascii=False)[:420])
            break
    if ini == evs[0][0]:
        print("   TODOS los nombres:", " | ".join(nombres)[:2500])
print("bytes descargados: %.2f MB" % (TOTAL[0] / 1048576.0))
