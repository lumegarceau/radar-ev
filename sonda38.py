"""Sonda Betinia/Altenar SIN navegador: solo peticiones HTTP a traves del proxy espanol.
Busca ligas, partidos y mercados de jugador."""
import json
import os
import re
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


print("== menu de deportes")
menu = get("widget/GetSportMenu")
if menu:
    print("claves:", list(menu)[:10] if isinstance(menu, dict) else type(menu))
    champs = menu.get("champs") if isinstance(menu, dict) else None
    print("campeonatos:", len(champs) if champs else None, "| ejemplo:", json.dumps((champs or [None])[0], ensure_ascii=False)[:250])
    ligas = {}
    for c in (champs or []):
        n = str(c.get("name"))
        if re.search(r"champions|europa league|laliga|la liga|premier|serie a|bundesliga|ligue 1|argent|liga f\b|femen|eredivisie|primeira|championship|segunda", n, re.I):
            ligas[c.get("id")] = n
    print("ligas de interes:", dict(list(ligas.items())[:40]))
else:
    ligas = {}

print("== partidos por liga")
ev_ejemplo = None
for cid, n in list(ligas.items())[:6]:
    j = get("widget/GetEvents", champIds=cid, sportId=66) or {}
    evs = j.get("events") or []
    if not evs:
        j = get("widget/GetUpcoming", champIds=cid, sportId=66, eventCount=20) or {}
        evs = j.get("events") or []
    print(" ", n, "(", cid, ") ->", len(evs), "partidos |", [e.get("name") for e in evs[:2]])
    if evs and not ev_ejemplo:
        ev_ejemplo = (n, evs[0])

if ev_ejemplo:
    n, e = ev_ejemplo
    print("== detalle de", e.get("name"), "id", e.get("id"))
    d = get("widget/GetEventDetails", eventId=e.get("id"))
    if d:
        print("claves:", list(d)[:15] if isinstance(d, dict) else type(d))
        mk = d.get("markets") or []
        print("mercados:", len(mk))
        tipos = {}
        for m in mk:
            nm = str(m.get("name"))
            tipos[nm] = tipos.get(nm, 0) + 1
        jug = {k: v for k, v in tipos.items() if PAL.search(k)}
        print("mercados con palabras de jugador:", len(jug))
        for k, v in list(jug.items())[:30]:
            print("   -", k, "| lineas/jugadores:", v)
        print("primeros mercados:", list(tipos)[:12])
        pj = [m for m in mk if PAL.search(str(m.get("name")))]
        print("ejemplo de mercado de jugador:", json.dumps(pj[0], ensure_ascii=False)[:500] if pj else None)
        odds = d.get("odds") or []
        print("cuotas en el detalle:", len(odds), "| ejemplo:", json.dumps(odds[:2], ensure_ascii=False)[:250])
print("bytes descargados: %.2f MB" % (TOTAL[0] / 1048576.0))
