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


def ops(cuerpo):
    return re.findall(r'"operationName"\s*:\s*"([^"]+)"', cuerpo or "")


def main():
    ip_publica()
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=PROXY)
        # 1) listado, para sacar direcciones de partidos
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 2500})
        pg = ctx.new_page()
        pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
        bag = []
        pg.on("response", lambda r: bag.append(r.text()) if ("bff-gql" in r.url and "json" in (r.headers.get("content-type") or "")) else None)
        pg.goto("https://www.betfair.es/apuestas/f%C3%BAtbol/s-1", timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(15000)
        urls = []
        for t in bag:
            for u in re.findall(r'f%C3%BAtbol/[^"\\?]+/e-\d+', t):
                if u not in urls:
                    urls.append(u)
        ctx.close()
        print("partidos en el listado:", len(urls))
        for u in urls[:12]:
            print("   ", urllib.parse.unquote(u))
        if not urls:
            return
        # 2) partido con el plan B
        ctx2 = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 3000})
        ctx2.add_init_script(STEALTH)
        pg2 = ctx2.new_page()
        pg2.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
        got = []
        def resp(r):
            try:
                if "bff-gql" in r.url and "json" in (r.headers.get("content-type") or ""):
                    got.append((r.request.post_data or "", r.text()))
            except Exception:
                pass
        pg2.on("response", resp)
        url0 = "https://www.betfair.es/apuestas/" + urls[0]
        pg2.goto(url0, timeout=60000, wait_until="domcontentloaded")
        for i in range(8):
            pg2.wait_for_timeout(4000)
            if "momento" not in pg2.title().lower():
                break
        pg2.wait_for_timeout(8000)
        print("\nPARTIDO:", pg2.title(), "| respuestas GQL:", len(got))
        def informe(et):
            print("\n--", et, "| GQL:", len(got))
            for cuerpo, t in got:
                o = ops(cuerpo)
                hit = sorted(set(m.group(0).lower() for m in MK.finditer(t)))
                print("   ops:", o[:6], "| bytes:", len(t), "| palabras:", hit[:8])
        informe("pagina principal del partido")
        # pestañas
        tabs = []
        try:
            for a in pg2.locator('a[href*="tabId="]').all()[:40]:
                h = a.get_attribute("href") or ""
                tx = " ".join((a.inner_text() or "").split())[:30]
                if (h, tx) not in tabs:
                    tabs.append((h, tx))
        except Exception as e:
            print("pestañas falla", repr(e)[:100])
        print("\npestañas encontradas:", len(tabs))
        for h, tx in tabs:
            print("   ", repr(tx), h[-60:])
        body = " ".join(pg2.inner_text("body").split())
        k = body.find("Resumen")
        print("\ntexto tras 'Resumen':", body[k:k + 700] if k >= 0 else body[600:1300])
        vistos = 0
        for h, tx in tabs:
            if not re.search(r"jugador|tiro|remate|falta|todo|player|shot", tx, re.I):
                continue
            vistos += 1
            if vistos > 4:
                break
            n0 = len(got)
            try:
                full = h if h.startswith("http") else "https://www.betfair.es" + (h if h.startswith("/") else "/apuestas/" + h)
                pg2.goto(full, timeout=60000, wait_until="domcontentloaded")
                pg2.wait_for_timeout(12000)
            except Exception as e:
                print("   falla pestaña", tx, repr(e)[:100])
            informe("pestaña " + tx + " (nuevas: %d)" % (len(got) - n0))
            tt = " ".join(pg2.inner_text("body").split())
            for m in MK.finditer(tt):
                print("   texto:", tt[max(0, m.start() - 80):m.start() + 220])
                break
        # volcado de la mejor respuesta con mercados de jugador
        best = None
        for cuerpo, t in got:
            if re.search(r"tiros? a puerta|remates?|faltas", t, re.I) and (best is None or len(t) > len(best[1])):
                best = (cuerpo, t)
        if best:
            print("\nMEJOR RESPUESTA ops:", ops(best[0]), "| bytes", len(best[1]))
            print("CUERPO:", best[0][:900])
            m = re.search(r"tiros? a puerta|remates?|faltas", best[1], re.I)
            print("MUESTRA:", best[1][max(0, m.start() - 700):m.start() + 1500])
        ctx2.close()
        br.close()


main()
