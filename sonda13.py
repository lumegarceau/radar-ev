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
    pg._post = {}
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
                pg._json.append((r.url, r.text(), r.request.method)); pg._post[r.url + "#" + str(len(pg._json))] = (r.request.post_data or "")[:1500]
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


def betfair(br):
    print("\n===== Betfair a fondo", flush=True)
    ctx, pg = nueva(br)
    if not ir(pg, "https://www.betfair.es/apuestas/f%C3%BAtbol/s-1", 12000):
        ctx.close()
        return
    cookies(pg)
    pg.wait_for_timeout(10000)
    gasto(pg, "Betfair listado")
    print("  peticiones de datos (GraphQL):")
    n = 0
    for (k, body), (u, c, m) in zip(list(pg._post.items()), pg._json):
        if "bff-gql" in u and n < 6:
            n += 1
            print("   -", m, u[:170], "| respuesta", len(c))
            print("     CUERPO:", body[:700].replace("\n", " "))
    pares = {}
    rx = re.compile(r'"viewUrn":"([^"]+)","viewUrl":"([^"]+)"')
    for u, c, m in pg._json:
        for urn, url in rx.findall(c):
            pares[urn] = url
    tipos = {}
    for urn in pares:
        t = urn.split("view:")[-1].split(":")[0]
        tipos[t] = tipos.get(t, 0) + 1
    print("  tipos de vista:", tipos)
    ev = [(urn, url) for urn, url in pares.items() if ":event" in urn or "/e-" in url or "partido" in urn]
    print("  vistas de partido:", len(ev))
    for urn, url in ev[:12]:
        print("    ", urn[:90], "->", url[:120])
    if not ev:
        for urn, url in list(pares.items())[:25]:
            print("    otro:", urn[:80], "->", url[:100])
    urls = ["/" + url for urn, url in ev]
    for u, c, m in pg._json:
        if "bff-gql" in u and len(c) > 30000:
            for marca in ('"eventId"', '"marketId"', '"urn"', '"nodeId"'):
                k = c.find(marca)
                if k >= 0:
                    print("  muestra", marca, ":", c[max(0, k - 300):k + 500].replace("\n", " "))
                    break
            break
    if not urls:
        try:
            print("  texto:", " ".join(pg.inner_text("body").split())[:600])
        except Exception:
            pass
        ctx.close()
        return
    pref = [x for x in urls if re.search(r"nations|champions|liga|premier|serie|bundes|ligue|europa", x, re.I)]
    dest = "https://www.betfair.es" + (pref or urls)[0]
    pg._json.clear()
    pg._post.clear()
    pg._bytes[0] = 0
    print("\n PARTIDO:", dest)
    if not ir(pg, dest, 20000):
        ctx.close()
        return
    for t in ("Jugadores", "Tiros", "Apuestas de jugador", "Especiales", "Estadísticas"):
        try:
            l = pg.get_by_text(t, exact=True).first
            if l.count():
                l.click(timeout=2500)
                pg.wait_for_timeout(3500)
                print("  pulsado:", t)
        except Exception:
            pass
    gasto(pg, "Betfair partido")
    mercados(pg)
    n = 0
    for (k, body), (u, c, m) in zip(list(pg._post.items()), pg._json):
        if "bff-gql" in u and n < 5:
            n += 1
            print("   - GQL", u[:150], "| respuesta", len(c), "| CUERPO:", body[:500].replace("\n", " "))
    for u, c, m in pg._json:
        for marca in ("Tiros a puerta", "Tiros", "Faltas"):
            k = c.find(marca)
            if k >= 0 and "bff-gql" in u:
                print("  MUESTRA de", marca, "en", u[:90], ":", c[max(0, k - 500):k + 900].replace("\n", " "))
                raise StopIteration
    try:
        print("  texto del partido:", " ".join(pg.inner_text("body").split())[:900])
    except Exception:
        pass
    ctx.close()


if not P.hostname:
    print("Falta el secreto PROXY_URL")
    raise SystemExit(1)
ip_publica()
with sync_playwright() as pw:
    br = pw.chromium.launch(proxy=PROXY)
    try:
        betfair(br)
    except StopIteration:
        pass
    except Exception as e:
        print("falla", repr(e)[:200])
    br.close()
print("\nTOTAL GASTADO: %.2f MB" % SESION["mb"])
