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
        print("\n===== Retabet (portada)")
        ctx, pg = nueva(br)
        try:
            r = pg.goto("https://www.retabet.es/", timeout=60000, wait_until="domcontentloaded")
            print("  estado:", r.status if r else None)
            pg.wait_for_timeout(15000)
            informe(pg, "portada")
            if "seguridad" not in pg.title().lower():
                hs = [a.get_attribute("href") for a in pg.locator("a[href]").all()[:300]]
                dep = [h for h in hs if h and re.search(r"deport|apuest|futbol|sport", h, re.I)][:15]
                print("   enlaces de apuestas:", dep)
        except Exception as e:
            print("  falla", repr(e)[:120])
        ctx.close()
        print("\n===== Luckia (donde esta el sportsbook)")
        ctx, pg = nueva(br)
        try:
            pg.goto("https://www.luckia.es/apuestas/futbol/", timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            for tx in ("Aceptar",):
                try:
                    pg.get_by_text(tx, exact=True).first.click(timeout=3000)
                except Exception:
                    pass
            pg.wait_for_timeout(8000)
            hs = []
            for a in pg.locator("a[href]").all()[:600]:
                h = a.get_attribute("href") or ""
                if h and h not in hs:
                    hs.append(h)
            ap = [h for h in hs if re.search(r"apuestas|sport|deporte|directo|vivo|futbol", h, re.I)]
            print("   enlaces:", len(hs), "| de apuestas:", ap[:25])
            print("   iframes:", [(f.url[:90]) for f in pg.frames])
            print("   scripts con sport/kambi/altenar/betby:", sorted(set(h for h in pg._h if re.search(r"kambi|altenar|betby|digitain|sport|bet|odds|sb", h, re.I)))[:15])
            informe(pg, "futbol")
            # probar el primer enlace de apuestas que sea otra direccion
            for h in ap:
                full = h if h.startswith("http") else "https://www.luckia.es" + h
                if full.rstrip("/") == pg.url.rstrip("/") or "/apuestas/futbol" in full:
                    continue
                pg._h.clear(); pg._j.clear()
                try:
                    pg.goto(full, timeout=60000, wait_until="domcontentloaded")
                    pg.wait_for_timeout(15000)
                    informe(pg, "siguiente")
                except Exception as e:
                    print("   falla", full[:80], repr(e)[:80])
                break
        except Exception as e:
            print("  falla", repr(e)[:120])
        ctx.close()
        br.close()


main()
