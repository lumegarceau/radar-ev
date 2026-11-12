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



SITIOS = [
    ("Retabet", ["https://www.retabet.es/apuestas/futbol", "https://www.retabet.es/"]),
    ("Luckia", ["https://www.luckia.es/apuestas/futbol/", "https://www.luckia.es/apuestas/"]),
]


def sitio(br, nombre, urls):
    print("\n=====", nombre)
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 2500})
    ctx.add_init_script(STEALTH)
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
    js, byts = [], [0]
    def resp(r):
        try:
            ct = (r.headers.get("content-type") or "").lower()
            if "json" in ct or "javascript" in ct and False:
                js.append((r.url, r.request.method, r.text(), r.request.post_data or ""))
        except Exception:
            pass
    def fin(rq):
        try:
            sz = rq.sizes(); byts[0] += (sz.get("responseBodySize") or 0)
        except Exception:
            pass
    pg.on("response", resp)
    pg.on("requestfinished", fin)
    ok = False
    for u in urls:
        try:
            r = pg.goto(u, timeout=60000, wait_until="domcontentloaded")
            print("  ", u, "-> estado", r.status if r else None, "| final:", pg.url[:110])
            for _ in range(6):
                pg.wait_for_timeout(4000)
                if "momento" not in pg.title().lower():
                    break
            ok = True
            break
        except Exception as e:
            print("  ", u, "falla", repr(e)[:90])
    if not ok:
        ctx.close(); return
    for tx in ("Aceptar todas", "Aceptar todo", "Aceptar", "Accept"):
        try:
            b = pg.get_by_text(tx, exact=False).first
            if b.count():
                b.click(timeout=3000); print("   cookies:", tx); break
        except Exception:
            pass
    pg.wait_for_timeout(15000)
    print("   titulo:", pg.title()[:80])
    print("   marcos (iframes):", [f.url[:100] for f in pg.frames][:8])
    hosts = {}
    for u, m, t, pd in js:
        h = urllib.parse.urlparse(u).netloc
        hosts.setdefault(h, [0, 0]); hosts[h][0] += 1; hosts[h][1] += len(t)
    print("   dominios con JSON:", {h: tuple(v) for h, v in sorted(hosts.items(), key=lambda kv: -kv[1][1])[:10]})
    grandes = sorted(js, key=lambda x: -len(x[2]))[:6]
    for u, m, t, pd in grandes:
        hit = sorted(set(x.group(0).lower() for x in re.finditer(r"tiro|remate|falta|jugador|player|shots?|fouls?", t, re.I)))
        print("   -", m, u[:150], "| bytes", len(t), "| palabras:", hit[:6])
        if pd:
            print("       cuerpo:", pd[:200])
    txt = " ".join(pg.inner_text("body").split())
    print("   texto de la pagina:", txt[:500])
    print("   enlaces de partido:", pg.locator('a[href*="partido"], a[href*="/evento"], a[href*="event"]').count())
    print("   MB aprox: %.2f" % (byts[0] / 1048576.0))
    ctx.close()


def main():
    ip_publica()
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=PROXY)
        for n, u in SITIOS:
            try:
                sitio(br, n, u)
            except Exception as e:
                print(n, "fallo", repr(e)[:150])
        br.close()


main()
