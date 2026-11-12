"""Sonda con proxy español: ¿se leen Luckia, Betsson, Betfair y PokerStars? ¿Cuántos MB gasta cada una?"""
import os
import re
import json
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
RAW = os.environ.get("PROXY_URL", "")
VAL = "".join(RAW.split())
if VAL and "://" not in VAL:
    VAL = "http://" + VAL
if VAL.startswith("http://http"):
    VAL = VAL[len("http://"):]
print("secreto recibido:", "si" if RAW else "NO", "| caracteres:", len(RAW),
      "| espacios o saltos:", len(RAW) - len(VAL.replace("http://", "", 1)) if RAW else 0)
if VAL:
    pre = VAL.split("@")[0]
    print("forma:", "http://" if VAL.startswith("http") else "?",
          "| tiene @:", "@" in VAL, "| usuario:", pre.split("//")[-1].split(":")[0][:40],
          "| host:", VAL.split("@")[-1][:40])
P = urllib.parse.urlparse(VAL)
PROXY = {"server": "%s://%s:%s" % (P.scheme or "http", P.hostname, P.port),
         "username": urllib.parse.unquote(P.username or ""),
         "password": urllib.parse.unquote(P.password or "")}
def ip_publica():
    try:
        h = urllib.request.ProxyHandler({"http": P.geturl(), "https": P.geturl()})
        o = urllib.request.build_opener(h)
        ip = json.loads(o.open("https://api.ipify.org?format=json", timeout=30).read())["ip"]
        g = json.loads(o.open("http://ip-api.com/json/" + ip + "?fields=country,city,isp,hosting", timeout=30).read())
        print("IP del proxy:", ip, g)
    except Exception as e:
        print("no puedo comprobar la IP del proxy:", repr(e)[:150])


SITIOS = [
    ("Betsson", ["https://www.betsson.es/apuestas-deportivas/futbol", "https://www.betsson.es/es/apuestas-deportivas/futbol"]),
    ("Betfair", ["https://www.betfair.es/apuestas/f%C3%BAtbol/s-1"]),
    ("Luckia", ["https://www.luckia.es/apuestas/futbol/", "https://www.luckia.es/apuestas/"]),
]
def ip_publica():
    try:
        h = urllib.request.ProxyHandler({"http": P.geturl(), "https": P.geturl()})
        o = urllib.request.build_opener(h)
        ip = json.loads(o.open("https://api.ipify.org?format=json", timeout=30).read())["ip"]
        g = json.loads(o.open("http://ip-api.com/json/" + ip + "?fields=country,city,isp,hosting", timeout=30).read())
        print("IP del proxy:", ip, g)
    except Exception as e:
        print("no puedo comprobar la IP del proxy:", repr(e)[:150])


PESADO = ("image", "media", "font")
SESION = {"mb": 0.0}
RX_NOM = re.compile(r'"(?:eventName|name|label|title)"\s*:\s*"([^"]{3,45}\s(?:-|v|vs\.?)\s[^"]{3,45})"')
RX_MK = re.compile(r'"(?:label|name|marketName|title|groupLabel)"\s*:\s*"([^"]*(?:[Tt]iro|[Rr]emate|[Ff]alta|[Pp]arada|[Jj]ugador|[Dd]isparo|[Pp]uerta|[Aa]l arco)[^"]*)"')


def nueva(br):
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2500})
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
    pg._json = []
    pg._bytes = [0]

    def fin(rq):
        try:
            sz = rq.sizes()
            pg._bytes[0] += (sz.get("responseBodySize") or 0) + (sz.get("responseHeadersSize") or 0)
        except Exception:
            pass

    def resp(r):
        try:
            if "json" in (r.headers.get("content-type") or "").lower():
                pg._json.append((r.url, r.text(), r.request.method))
        except Exception:
            pass

    pg.on("requestfinished", fin)
    pg.on("response", resp)
    return ctx, pg


def ir(pg, url, espera=15000):
    try:
        r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
        print("  estado:", r.status if r else None, "| final:", pg.url[:140])
    except Exception as e:
        print("  no carga:", repr(e)[:120])
        return False
    pg.wait_for_timeout(espera)
    return True


def cookies(pg):
    for t in ("Aceptar todas las cookies", "Aceptar todas", "Aceptar", "Entendido"):
        try:
            l = pg.get_by_text(t, exact=False).first
            if l.count():
                l.click(timeout=3000)
                pg.wait_for_timeout(2500)
                print("  cookies aceptadas con:", t)
                return
        except Exception:
            pass


def gasto(pg, et):
    mb = pg._bytes[0] / 1048576.0
    SESION["mb"] += mb
    print("  [%s] gastado %.2f MB | JSON: %d" % (et, mb, len(pg._json)))


def nombres(pg):
    vis = []
    for u, c, m in pg._json:
        for x in RX_NOM.findall(c):
            if x not in vis:
                vis.append(x)
    return vis


def mercados(pg):
    cnt = {}
    for u, c, m in pg._json:
        for x in RX_MK.findall(c):
            cnt[x] = cnt.get(x, 0) + 1
    print("  mercados con tiros/remates/faltas/paradas/jugador/puerta (%d distintos):" % len(cnt))
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:40]:
        print("     -", k[:90], "x", v)
    big = sorted(pg._json, key=lambda x: -len(x[1]))[:6]
    for u, c, m in big:
        print("  JSON grande:", m, u[:150], "| tam:", len(c))


def trozo(txt, marca, ant=300, des=900):
    k = txt.find(marca)
    return None if k < 0 else txt[max(0, k - ant):k + des]


def enmascara(t):
    return re.sub(r'("(?:[Tt]oken|sessionToken|sessiontoken)"\\s*:\\s*")[^"]{8,}', r'\\1***', t)


def betsson(br):
    print("\n===== Betsson partido", flush=True)
    ctx, pg = nueva(br)
    if not ir(pg, "https://www.betsson.es/apuestas-deportivas/futbol"):
        ctx.close()
        return
    cookies(pg)
    pg.wait_for_timeout(8000)
    gasto(pg, "Betsson listado")
    evs = []
    for u, c, m in pg._json:
        if "events-table" not in u:
            continue
        try:
            j = json.loads(c)
        except Exception:
            continue
        fase = "Live" if "eventPhase=Live" in u else "Otra"

        def busca(x, prof=0):
            if prof > 8:
                return
            if isinstance(x, dict):
                if x.get("slug") and x.get("participants"):
                    evs.append((fase, x))
                    return
                for v in x.values():
                    busca(v, prof + 1)
            elif isinstance(x, list):
                for v in x:
                    busca(v, prof + 1)
        busca(j)
    print("  eventos vistos:", len(evs), "| fases:", sorted(set(f for f, _ in evs)))
    if evs:
        print("  claves de un evento:", sorted(evs[0][1].keys())[:40])
    cand = [e for f, e in evs if e.get("slug") and len(e.get("subParticipants") or []) > 10]
    pre = [e for f, e in evs if f != "Live" and e.get("slug")]
    e = (pre or cand or [None])[0]
    if not e:
        ctx.close()
        return
    print("  elegido:", e.get("slug"), "| claves de fecha:", {k: e[k] for k in e if "ate" in k or "tart" in k or "hase" in k})
    pg._json.clear()
    pg._bytes[0] = 0
    if not ir(pg, "https://www.betsson.es/apuestas-deportivas/" + e["slug"], 18000):
        ctx.close()
        return
    for t in ("Jugadores", "Tiros", "Especiales", "Más mercados", "Todos"):
        try:
            l = pg.get_by_text(t, exact=True).first
            if l.count():
                l.click(timeout=2500)
                pg.wait_for_timeout(3000)
        except Exception:
            pass
    gasto(pg, "Betsson partido")
    mercados(pg)
    nom = (e.get("subParticipants") or [{}])[0].get("label", "")
    for u, c, m in pg._json:
        if "event-market" in u or "market" in u.split("?")[0]:
            for jug in [x.get("label") for x in (e.get("subParticipants") or [])[:40]]:
                if jug and jug in c:
                    k = c.find(jug)
                    print(" MERCADO con jugador:", m, u[:200], "| jugador:", jug, "| tam", len(c))
                    print("   ", c[max(0, k - 900):k + 900].replace("\n", " ")[:1800])
                    raise StopIteration
    ctx.close()


def betfair(br):
    print("\n===== Betfair partido", flush=True)
    ctx, pg = nueva(br)
    if not ir(pg, "https://www.betfair.es/apuestas/f%C3%BAtbol/s-1"):
        ctx.close()
        return
    cookies(pg)
    pg.wait_for_timeout(8000)
    malas = re.compile(r"Femenin|\\(W\\)|Serie|Cup|Liga|League|Games|UEFA|Plataforma|Platform|Brasil", re.I)
    cands = []
    for n in nombres(pg):
        izq, _, der = n.partition(" - ")
        if der and not malas.search(n) and izq not in cands:
            cands.append(izq)
    print("  candidatos:", cands[:8])
    for izq in cands[:5]:
        pg._json.clear()
        pg._bytes[0] = 0
        try:
            pg.get_by_text(izq, exact=True).first.click(timeout=4000)
        except Exception as e:
            print("  no pude pulsar", izq, repr(e)[:70])
            continue
        pg.wait_for_timeout(12000)
        print("  pulsado:", izq, "| url:", pg.url[:150])
        if "/s-1" in pg.url and pg.url.rstrip("/").endswith("s-1"):
            continue
        for t in ("Jugadores", "Remates", "Tiros", "Especiales", "Más mercados"):
            try:
                l = pg.get_by_text(t, exact=True).first
                if l.count():
                    l.click(timeout=2500)
                    pg.wait_for_timeout(3000)
            except Exception:
                pass
        gasto(pg, "Betfair partido")
        mercados(pg)
        print("  texto:", " ".join(pg.inner_text("body").split())[:600])
        break
    ctx.close()


if not P.hostname:
    print("Falta el secreto PROXY_URL")
    raise SystemExit(1)
ip_publica()
with sync_playwright() as pw:
    br = pw.chromium.launch(proxy=PROXY)
    for f in (betsson,):
        try:
            f(br)
        except StopIteration:
            pass
        except Exception as e:
            print(f.__name__, "falla", repr(e)[:150])
    br.close()
print("\nTOTAL GASTADO: %.2f MB" % SESION["mb"])
