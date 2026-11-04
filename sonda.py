import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es"
IDS = ["17397080", "17397584"]
RUTAS = [
    "/es/es/sports/evt/{}",
    "/es/es/sports/event/{}",
    "/es/es/sports/evt/{}/markets",
    "/es/sports/evt/{}",
]
CLAVES = re.compile(r"c[oó]rner|esquina|tarjeta|remate|tiros|faltas", re.I)

with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 1400})
    pg = ctx.new_page()
    pg.goto(BASE + "/es/es/sports", timeout=60000,
            wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    try:
        pg.locator("#onetrust-accept-btn-handler").first.click(timeout=4000)
    except Exception:
        pass
    hecho = False
    for eid in IDS:
        for ruta in RUTAS:
            u = BASE + ruta.format(eid)
            try:
                r = pg.goto(u, timeout=45000, wait_until="domcontentloaded")
                pg.wait_for_timeout(12000)
            except Exception as e:
                print(u, "fallo", repr(e)[:100])
                continue
            t = pg.inner_text("body")
            ok = bool(CLAVES.search(t))
            print(u, "->", r.status if r else None, "| texto", len(t),
                  "| palabras clave:", ok, "|", pg.title()[:50])
            if ok and not hecho:
                hecho = True
                print("\n--- Lineas con palabras clave ---")
                n = 0
                for ln in t.split("\n"):
                    if CLAVES.search(ln) and n < 60:
                        n += 1
                        print(" ", ln[:120])
                print("\n--- TEXTO (3000 car.) ---")
                print(t[900:3900].replace("\n", " | "))
        if hecho:
            break
    if not hecho:
        print("\nNingun intento mostro mercados. Texto del ultimo:")
        print(pg.inner_text("body")[:1500].replace("\n", " | "))
    br.close()
print("fin")
