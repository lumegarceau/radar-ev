"""Cuotas de Betinia (plataforma Altenar) sin navegador: peticiones HTTP a traves del proxy espanol.
Lee remates y remates a puerta de jugador de los partidos de las proximas horas.
Salida: betinia.json con el mismo formato que las demas casas."""
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://sb2frontend-altenar2.biahosted.com/api/"
Q = {"culture": "es-ES", "timezoneOffset": "-60", "integration": "betiniaes", "deviceType": "1",
     "numFormat": "en-GB", "countryCode": "ES"}
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HORAS = 36           # solo partidos que empiezan en las proximas horas (los props salen ~1 dia antes)
MAX_EVENTOS = 45
LIMITE_S = 12 * 60
SPORT_FUTBOL = 66
# campeonatos verificados en la sonda
CHAMPS = {16808: "Champions", 16809: "Europa League", 2941: "LaLiga", 3111: "LaLiga 2",
          2936: "Premier", 2937: "Championship", 2942: "Serie A", 2950: "Bundesliga",
          2943: "Ligue 1", 3152: "Primeira Liga", 3065: "Eredivisie", 11318: "Brasileirao"}
# paises/ligas extra que se buscan en el menu (se imprimen para poder ajustarlos)
EXTRA_PAISES = re.compile(r"b[eé]lgica|turqu[ií]a|dinamarca|argentina", re.I)
EXTRA_LIGA = re.compile(r"pro league|s[uü]per lig|superliga|liga profesional|primera divisi[oó]n|primera nacional", re.I)
EXTRA_NO = re.compile(r"femenin|copa|sub[- ]?\d|u\d\d|reserva|juvenil|amistoso|2\.|segunda", re.I)
# mercado padre -> estadistica del radar
STAT = {"Remates a Puerta": "sot", "Remates": "shots"}
RE_HIJO = re.compile(r"^(?:Remates a Puerta|Remates)\s*-\s*(.+?)\s*\(([A-Z0-9]{2,5})\)\s*$")
RE_EQ = re.compile(r"\s+vs\.?\s+", re.I)
T0 = time.time()
BYTES = [0]
raw = "".join(os.environ.get("PROXY_URL", "").split())
if raw and "://" not in raw:
    raw = "http://" + raw
OP = urllib.request.build_opener(urllib.request.ProxyHandler({"http": raw, "https": raw})) if raw else urllib.request.build_opener()


def get(ruta, **extra):
    url = BASE + ruta + "?" + urllib.parse.urlencode(dict(Q, **extra))
    rq = urllib.request.Request(url, headers={"User-Agent": UA, "Origin": "https://betinia.es",
                                              "Referer": "https://betinia.es/"})
    for intento in range(3):
        try:
            b = OP.open(rq, timeout=40).read()
            BYTES[0] += len(b)
            return json.loads(b)
        except Exception as e:
            if intento == 2:
                print("  falla", ruta, extra, repr(e)[:100])
            time.sleep(2)
    return None


def plano(x):
    if isinstance(x, list):
        out = []
        for y in x:
            out += plano(y)
        return out
    return [x]


def limpia(s):
    return " ".join(str(s).split())


def jugadores_de(d):
    """Del detalle de un partido saca [(stat, jugador, n, cuota)] de remates y remates a puerta."""
    hijos = {c.get("id"): c for c in (d.get("childMarkets") or [])}
    odds = {o.get("id"): o for o in (d.get("odds") or [])}
    out = {}
    for m in d.get("markets") or []:
        stat = STAT.get(limpia(m.get("name")))
        if not stat:
            continue
        for cid in m.get("childMarketIds") or []:
            c = hijos.get(cid)
            if not c:
                continue
            mt = RE_HIJO.match(limpia(c.get("name")))
            if not mt:
                continue
            nombre = mt.group(1).strip()
            for oid in plano(c.get("desktopOddIds") or c.get("mobileOddIds") or []):
                o = odds.get(oid)
                if not o or o.get("oddStatus", 0) != 0:
                    continue
                try:
                    linea = float(o.get("sv"))
                    precio = float(o.get("price"))
                except (TypeError, ValueError):
                    continue
                if precio <= 1.0 or linea % 1 != 0.5 or limpia(o.get("name")).lower().startswith("menos"):
                    continue
                n = int(linea + 0.5)
                out[(stat, nombre, n)] = precio
    return [[s, nom, n, c] for (s, nom, n), c in out.items()]


def champs_extra():
    menu = get("widget/GetSportMenu") or {}
    cats = {c.get("id"): limpia(c.get("name")) for c in (menu.get("categories") or [])}
    ex = {}
    for c in menu.get("champs") or []:
        n = limpia(c.get("name"))
        pais = cats.get(c.get("catId"), "")
        if c.get("id") in CHAMPS or not c.get("eventsCount"):
            continue
        if EXTRA_PAISES.search(pais) and EXTRA_LIGA.search(n) and not EXTRA_NO.search(n):
            ex[c["id"]] = pais + " " + n
    return ex


def main():
    ahora = datetime.now(timezone.utc)
    camps = dict(CHAMPS)
    try:
        ex = champs_extra()
        print("betinia: ligas extra:", ex)
        camps.update(ex)
    except Exception as e:
        print("betinia: menu falla:", repr(e)[:80])
    evs = []
    for cid, nom in camps.items():
        j = get("widget/GetEvents", champIds=cid, sportId=SPORT_FUTBOL) or {}
        lst = j.get("events") or []
        if not lst:
            j = get("widget/GetUpcoming", champIds=cid, sportId=SPORT_FUTBOL, eventCount=30) or {}
            lst = j.get("events") or []
        n_ok = 0
        for e in lst:
            try:
                ini = datetime.fromisoformat(e["startDate"].replace("Z", "+00:00"))
            except Exception:
                continue
            h = (ini - ahora).total_seconds() / 3600
            if 0 < h <= HORAS:
                evs.append((ini, nom, e))
                n_ok += 1
        print("betinia:", nom, "->", len(lst), "partidos |", n_ok, "en las proximas", HORAS, "h")
    evs.sort(key=lambda x: x[0])
    partidos = []
    for ini, nom, e in evs[:MAX_EVENTOS]:
        if time.time() - T0 > LIMITE_S:
            print("betinia: limite de tiempo, se corta")
            break
        eq = RE_EQ.split(limpia(e.get("name")))
        if len(eq) != 2:
            continue
        d = get("widget/GetEventDetails", eventId=e.get("id"))
        if not d:
            continue
        jug = jugadores_de(d)
        print("  ", limpia(e.get("name")), "|", ini.strftime("%d/%m %H:%M UTC"), "| mercados", len(d.get("markets") or []),
              "| cuotas de jugador", len(jug))
        if jug:
            partidos.append({"inicio": ini.timestamp(), "c1": eq[0], "c2": eq[1],
                             "equipo": [], "total": [], "jugador": jug})
    print("betinia: partidos con cuotas:", len(partidos), "| cuotas de jugador:", sum(len(p["jugador"]) for p in partidos))
    print("betinia: datos descargados: %.1f MB | %d s" % (BYTES[0] / 1048576.0, time.time() - T0))
    if partidos:
        json.dump({"ts": time.time(), "partidos": partidos}, open("betinia.json", "w"), ensure_ascii=False)
        print("guardado betinia.json")
    else:
        print("betinia: sin partidos con props; no se sobrescribe el archivo")


if __name__ == "__main__":
    main()
