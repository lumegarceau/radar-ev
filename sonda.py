import json
import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es"
CLAVES = re.compile(r"c[oó]rner|esquina|tarjeta|remate|tiros|faltas", re.I)
jsons = []
frames = []


def resp(r):
    try:
        if "json" not in r.headers.get("content-type", ""):
            return
        if "betway.es" not in r.url:
            return
        jsons.append((r.url, r.text()))
    except Exception:
        pass


def ws(w):
    print("WEBSOCKET", w.url[:150])

    def rec(d):
        frames.append(str(d)[:600])
    w.on("framereceived", rec)


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    pg.on("response", resp)
    pg.on("websocket", ws)
    pg.goto(BASE + "/es/sports/cpn/soccer/1", timeout=60000,
            wait_until="domcontentloaded")
    pg.wait_for_timeout(12000)
    print("URL:", pg.url, "|", pg.title()[:80])
    print("\n--- ENLACES de la pagina (primeros 40) ---")
    hrefs = pg.eval_on_selector_all(
        "a[href]", "e=>e.map(x=>x.getAttribute('href'))")
    vistos = []
    for h in hrefs:
        if h and "/sports" in h and h not in vistos:
            vistos.append(h)
    for h in vistos[:40]:
        print(h)
    print("\n--- JSON de getGroup (completo, hasta 2500 caracteres) ---")
    n = 0
    for u, t in jsons:
        if "getGroup" in u and n < 2:
            n += 1
            print(u)
            print(t[:2500])
    print("\n--- Texto visible de la pagina ---")
    print(pg.inner_text("body")[:1500].replace("\n", " | "))
    ev = [h for h in vistos if re.search(r"/event|/evt|/match|/e/", h)]
    print("\nENLACES que parecen partido:", ev[:10])
    if ev:
        jsons.clear()
        frames.clear()
        u = ev[0]
        if u.startswith("/"):
            u = BASE + u
        pg.goto(u, timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(12000)
        print("\n=== PARTIDO:", pg.url, "|", pg.title()[:80])
        print(pg.inner_text("body")[:2500].replace("\n", " | "))
        print("\n--- JSON con mercados ---")
        for u2, t in jsons:
            tag = "MERCADOS" if CLAVES.search(t) else "-"
            print(tag, len(t), u2[:150])
            if tag == "MERCADOS":
                m = CLAVES.search(t)
                a = max(0, m.start() - 400)
                print("   ...", t[a:a + 1200])
                break
        print("\n--- Mensajes websocket (primeros 12) ---")
        for f in frames[:12]:
            print(f)
    br.close()
print("fin")
