import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
EVT = "https://betway.es/es/es/sports/evt/17397080"
PESTANAS = ["Córners", "Jugadores", "Otros", "Goles", "1ª y 2ª mitad"]


def zona(t):
    a = t.find("Otros")
    b = t.find("Reglas sobre apuestas")
    if a < 0:
        a = 0
    if b < 0:
        b = len(t)
    return t[a:b]


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2000})
    pg = ctx.new_page()
    pg.goto(EVT, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(12000)
    try:
        pg.locator("#onetrust-accept-btn-handler").first.click(timeout=4000)
    except Exception:
        pass
    pg.wait_for_timeout(2000)
    for nombre in PESTANAS:
        print("\n" + "=" * 50)
        print("PESTANA:", nombre)
        loc = pg.get_by_text(nombre, exact=True)
        n = loc.count()
        print("coincidencias exactas:", n)
        if not n:
            continue
        try:
            html = loc.first.evaluate("e=>e.outerHTML")
            padre = loc.first.evaluate(
                "e=>e.parentElement?e.parentElement.outerHTML.slice(0,500)"
                ":''")
            print("HTML elemento:", html[:300])
            print("HTML padre:", padre)
            loc.first.click(timeout=10000)
            pg.wait_for_timeout(5000)
            t = pg.inner_text("body")
            z = zona(t).replace("\n", " | ")
            print("TEXTO tras pulsar (2500 car.):")
            print(z[:2500])
        except Exception as e:
            print("fallo", repr(e)[:300])
    br.close()
print("fin")
