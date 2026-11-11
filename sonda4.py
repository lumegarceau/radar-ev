"""Sonda con proxy español: ¿se leen Luckia, Betsson, Betfair y PokerStars? ¿Cuántos MB gasta cada una?"""
import os
import re
import json
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
P = urllib.parse.urlparse(os.environ.get("PROXY_URL", ""))
PROXY = {"server": "%s://%s:%s" % (P.scheme or "http", P.hostname, P.port),
         "username": urllib.parse.unquote(P.username or ""),
         "password": urllib.parse.unquote(P.password or "")}
URLS = [
    ("Luckia", "https://www.luckia.es/apuestas/"),
    ("Luckia deportes", "https://sports.luckia.es/"),
    ("Betsson", "https://www.betsson.es/apuestas-deportivas"),
    ("Betsson sportsbook", "https://sportsbook.betsson.es/"),
    ("Betfair", "https://www.betfair.es/sport/football"),
    ("PokerStars", "https://www.pokerstars.es/sports/"),
    ("PokerStars 2", "https://www.pokerstars.es/apuestas-deportivas/"),
]
CLAVES = ("odds", "price", "decimal", "cuota", "selection", "outcome", "market", "betOffer", "events")
PESADO = ("image", "media", "font")


def ip_publica():
    try:
        h = urllib.request.ProxyHandler({"http": P.geturl(), "https": P.geturl()})
        o = urllib.request.build_opener(h)
        ip = json.loads(o.open("https://api.ipify.org?format=json", timeout=30).read())["ip"]
        g = json.loads(o.open("http://ip-api.com/json/" + ip + "?fields=country,city,isp,hosting", timeout=30).read())
        print("IP del proxy:", ip, g)
    except Exception as e:
        print("no puedo comprobar la IP del proxy:", repr(e)[:150])


def sonda(br, nombre, url):
    print("\n=====", nombre, url, flush=True)
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2500})
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
    total = [0]
    vistos = []

    def fin(rq):
        try:
            s = rq.sizes()
            total[0] += (s.get("responseBodySize") or 0) + (s.get("responseHeadersSize") or 0)
        except Exception:
            pass

    def resp(r):
        try:
            if "json" not in (r.headers.get("content-type") or "").lower():
                return
            c = r.text()
            k = [x for x in CLAVES if x.lower() in c.lower()[:400000]]
            vistos.append((r.status, len(c), r.url[:150], k[:6]))
        except Exception:
            pass

    pg.on("requestfinished", fin)
    pg.on("response", resp)
    try:
        r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
        print("estado:", r.status if r else None, "| url final:", pg.url[:150])
    except Exception as e:
        print("no carga:", repr(e)[:150])
        ctx.close()
        return
    pg.wait_for_timeout(15000)
    try:
        t = re.sub(r"\s+", " ", pg.inner_text("body"))
        print("titulo:", pg.title()[:100], "| texto:", len(t), "caracteres")
        print("texto inicio:", t[:300])
    except Exception as e:
        print("lectura falla:", repr(e)[:100])
    vistos.sort(key=lambda x: -x[1])
    print("respuestas JSON:", len(vistos))
    for v in vistos[:12]:
        print("  ", v)
    print("DATOS GASTADOS en esta pagina: %.2f MB" % (total[0] / 1048576.0))
    ctx.close()
    return total[0]


if not P.hostname:
    print("Falta el secreto PROXY_URL")
    raise SystemExit(1)
ip_publica()
with sync_playwright() as pw:
    br = pw.chromium.launch(proxy=PROXY)
    gasto = 0
    for n, u in URLS:
        try:
            gasto += sonda(br, n, u) or 0
        except Exception as e:
            print(n, "falla", repr(e)[:100])
    print("\nTOTAL GASTADO: %.2f MB" % (gasto / 1048576.0))
    br.close()
