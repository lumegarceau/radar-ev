"""Sonda 3 Betinia/Altenar: estructura exacta de mercados de jugador: solo peticiones HTTP a traves del proxy espanol.
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

def plano(x):
    if isinstance(x, list):
        out = []
        for y in x:
            out += plano(y)
        return out
    return [x]


JUG = re.compile(r"remates?|tiros? a puerta|faltas?|fuera de juego|entradas?|tarjetas?|paradas?", re.I)
PAD = ["Remates a Puerta", "Remates", "Tarjetas", "Paradas del portero (incl. prórroga)", "Fuera de juego del jugador"]
ini, n, e = evs[0]
print("\n== DETALLE", e.get("name"), ini.strftime("%d/%m %H:%M UTC"))
d = get("widget/GetEventDetails", eventId=e.get("id"))
mk = d.get("markets") or []
print("competidores:", json.dumps(d.get("competitors"), ensure_ascii=False)[:300])
nombres = []
for m in mk:
    nm = str(m.get("name"))
    if nm not in nombres:
        nombres.append(nm)
print("TODOS los mercados con jugador/remates/faltas/tarjetas/etc (", len([x for x in nombres if JUG.search(x)]), "):")
for x in nombres:
    if JUG.search(x):
        print("   -", x)
ch = {c.get("id"): c for c in (d.get("childMarkets") or [])}
odds = {o.get("id"): o for o in (d.get("odds") or [])}
vistos = set()
for m in mk:
    nm = str(m.get("name"))
    quiere = nm in PAD or (re.search(r"falta", nm, re.I) and not re.search(r"1x2|equipo", nm, re.I))
    if not quiere or nm in vistos:
        continue
    vistos.add(nm)
    hijos = m.get("childMarketIds") or []
    print("\n##", nm, "| typeId", m.get("typeId"), "| hijos", len(hijos), "| sv", m.get("sv"), "| variant", m.get("variant"), "| headers", json.dumps(m.get("headers"), ensure_ascii=False)[:160])
    for cid in hijos[:3]:
        c = ch.get(cid) or {}
        ids = plano(c.get("desktopOddIds") or c.get("mobileOddIds") or [])
        print("   hijo:", c.get("name"), "| sv", c.get("sv"), "| variant", c.get("variant"))
        for oid in ids[:4]:
            o = odds.get(oid) or {}
            print("       cuota:", o.get("name"), "| typeId", o.get("typeId"), "| precio", o.get("price"), "| sv", o.get("sv"))
print("bytes descargados: %.2f MB" % (TOTAL[0] / 1048576.0))
