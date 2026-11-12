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



PESADO = ("image", "media", "font")
MK = re.compile(r"tiro|remate|falta|parada|jugador|puerta|arco", re.I)
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")



def nueva(br):
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 2500})
    ctx.add_init_script(STEALTH)
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
    pg._h, pg._j, pg._ws = {}, [], []
    pg.on("request", lambda r: pg._h.__setitem__(urllib.parse.urlparse(r.url).netloc, pg._h.get(urllib.parse.urlparse(r.url).netloc, 0) + 1))
    pg.on("websocket", lambda w: pg._ws.append(w.url))
    def resp(r):
        try:
            if "json" in (r.headers.get("content-type") or "").lower():
                pg._j.append((r.url, r.text()))
        except Exception:
            pass
    pg.on("response", resp)
    return ctx, pg


def informe(pg, et):
    print("  [%s] titulo: %s | url: %s" % (et, pg.title()[:60], pg.url[:100]))
    print("   dominios pedidos:", dict(sorted(pg._h.items(), key=lambda kv: -kv[1])[:14]))
    print("   websockets:", pg._ws[:5])
    for u, t in sorted(pg._j, key=lambda x: -len(x[1]))[:4]:
        hit = sorted(set(x.group(0).lower() for x in re.finditer(r"tiro|remate|falta|jugador|player|shots?|fouls?", t, re.I)))
        print("   JSON", u[:130], "| bytes", len(t), "|", hit[:5])
    print("   texto:", " ".join(pg.inner_text("body").split())[:300])



def main():
    ip_publica()
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=PROXY)
        ctx, pg = nueva(br)
        urls = []
        pg.on("request", lambda r: urls.append(r.url) if re.search(r"sbtech|sportsbook|sb-|/sb|odds|kambi|betradar|digitain", r.url, re.I) else None)
        pg.goto("https://www.luckia.es/apuestas/futbol/", timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(5000)
        try:
            pg.get_by_text("Aceptar", exact=True).first.click(timeout=3000)
        except Exception:
            pass
        pg.wait_for_timeout(10000)
        html = pg.content()
        print("tamano HTML:", len(html))
        print("peticiones con sbtech/odds:", urls[:15])
        for m in list(re.finditer(r"sbtech", html, re.I))[:6]:
            print("  HTML sbtech:", html[max(0, m.start() - 250):m.start() + 350].replace("\n", " "))
            print("  ---")
        print("scripts:", [s for s in re.findall(r'<script[^>]+src="([^"]+)"', html) if re.search(r"sbtech|sport|apuest|bet", s, re.I)][:15])
        print("elementos con id/clase sportsbook:", re.findall(r'(?:id|class)="([^"]*(?:sportsbook|sbtech|sb-|betting)[^"]*)"', html, re.I)[:12])
        # probar la pagina principal de apuestas y una liga
        for u in ("https://www.luckia.es/apuestas/", "https://www.luckia.es/apuestas/futbol/liga-espanola/"):
            urls.clear(); pg._h.clear(); pg._j.clear()
            try:
                pg.goto(u, timeout=60000, wait_until="domcontentloaded")
                pg.wait_for_timeout(15000)
                print("\n", u, "| titulo:", pg.title()[:60], "| peticiones sbtech/odds:", urls[:10])
                print("   dominios:", dict(sorted(pg._h.items(), key=lambda kv: -kv[1])[:10]), "| ws:", pg._ws[:3])
                print("   iframes:", [f.url[:100] for f in pg.frames][:6])
                print("   texto:", " ".join(pg.inner_text("body").split())[:200])
            except Exception as e:
                print("   falla", u, repr(e)[:80])
        ctx.close()
        br.close()


main()
