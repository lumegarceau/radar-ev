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
PATRON_EVENTO = ("/evento", "/event", "/partido", "/match", "/e-", "/f-", "/fixture", "/game")
PALABRAS = ("remates", "tiros a puerta", "tiros", "faltas cometidas", "faltas", "paradas", "disparos", "shots", "fouls")
PESADO = ("image", "media", "font")
SESION = {"mb": 0.0}


def nueva(br, extra_http2=False):
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
            if "json" not in (r.headers.get("content-type") or "").lower():
                return
            c = r.text()
            pg._json.append((r.url, c, dict(r.request.headers)))
        except Exception:
            pass

    pg.on("requestfinished", fin)
    pg.on("response", resp)
    return ctx, pg


def ir(pg, url, espera=15000):
    try:
        r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
        print("  estado:", r.status if r else None, "| final:", pg.url[:130])
    except Exception as e:
        print("  no carga:", repr(e)[:120])
        return False
    pg.wait_for_timeout(espera)
    return True


def informe(pg, etiqueta):
    print("  [%s] datos gastados: %.2f MB | respuestas JSON: %d" % (etiqueta, pg._bytes[0] / 1048576.0, len(pg._json)))
    SESION["mb"] += pg._bytes[0] / 1048576.0
    hits = {}
    for url, c, hd in pg._json:
        bajo = c.lower()
        for p in PALABRAS:
            if p in bajo:
                hits.setdefault(url, []).append(p)
    print("  direcciones de datos con mercados de remates/faltas/paradas:", len(hits))
    for url, ps in list(hits.items())[:10]:
        i = pg._json[[u for u, _, _ in pg._json].index(url)]
        txt = i[1]
        k = txt.lower().find(ps[0])
        print("   *", url[:170], "| palabras:", sorted(set(ps))[:6], "| tam:", len(txt))
        print("       contexto:", txt[max(0, k - 80):k + 120].replace("\n", " "))
        print("       cabeceras de la peticion:", sorted(k2 for k2 in i[2].keys() if not k2.startswith(":"))[:14])


def enlaces(pg):
    try:
        return pg.evaluate("""()=>Array.from(document.querySelectorAll('a[href]')).map(a=>({h:a.href,t:(a.innerText||'').trim().replace(/\\s+/g,' ').slice(0,70)})).filter(x=>x.h&&x.t)""")
    except Exception as e:
        print("  enlaces falla", repr(e)[:80])
        return []


def sitio(br, nombre, urls):
    print("\n=====", nombre, flush=True)
    ctx, pg = nueva(br)
    ok = False
    for u in urls:
        print(" listado:", u)
        if ir(pg, u):
            ok = True
            break
    if not ok:
        ctx.close()
        return
    informe(pg, nombre + " listado")
    L = enlaces(pg)
    print("  enlaces vistos:", len(L))
    ev = [x for x in L if any(p in x["h"] for p in PATRON_EVENTO) and (" - " in x["t"] or " v " in x["t"].lower() or " vs" in x["t"].lower())]
    print("  posibles partidos:", [(x["t"], x["h"][:90]) for x in ev[:6]])
    if not ev:
        print("  muestra de enlaces:", [(x["t"][:30], x["h"][:70]) for x in L[:25]])
        ctx.close()
        return
    dest = ev[0]["h"]
    print(" PARTIDO:", ev[0]["t"], dest[:130])
    pg._json.clear()
    pg._bytes[0] = 0
    if ir(pg, dest, 20000):
        try:
            for t in ("Jugadores", "Remates", "Tiros", "Especiales", "Más mercados", "Todos"):
                loc = pg.get_by_text(t, exact=False).first
                if loc.count():
                    loc.click(timeout=2500)
                    pg.wait_for_timeout(3000)
        except Exception:
            pass
        informe(pg, nombre + " partido")
        try:
            tx = pg.inner_text("body")
            print("  texto del partido (inicio):", " ".join(tx.split())[:500])
        except Exception:
            pass
    ctx.close()


if not P.hostname:
    print("Falta el secreto PROXY_URL")
    raise SystemExit(1)
ip_publica()
with sync_playwright() as pw:
    br = pw.chromium.launch(proxy=PROXY)
    for n, u in SITIOS:
        try:
            sitio(br, n, u)
        except Exception as e:
            print(n, "falla", repr(e)[:120])
    br.close()
    print("\nPokerStars sin HTTP/2:")
    br = pw.chromium.launch(proxy=PROXY, args=["--disable-http2"])
    ctx, pg = nueva(br)
    for u in ("https://www.pokerstars.es/sports/", "https://www.pokerstars.es/apuestas-deportivas/"):
        print(" ", u)
        if ir(pg, u, 10000):
            try:
                print("  texto:", " ".join(pg.inner_text("body").split())[:300])
            except Exception:
                pass
    informe(pg, "PokerStars")
    br.close()
print("\nTOTAL GASTADO: %.2f MB" % SESION["mb"])
