import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LIGA = "https://betway.es/es/es/sports/grp/soccer/spain/la-liga"
CLAVES = re.compile(r"c[oó]rner|esquina|tarjeta|remate|tiros|faltas", re.I)

with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 1400})
    pg = ctx.new_page()
    pg.goto(LIGA, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(10000)
    for sel in ("#onetrust-accept-btn-handler",
                "button:has-text('Aceptar todas')",
                "button:has-text('Aceptar')"):
        try:
            pg.locator(sel).first.click(timeout=4000)
            print("cookies aceptadas con", sel)
            break
        except Exception:
            pass
    pg.wait_for_timeout(3000)
    try:
        b = pg.get_by_text("VER", exact=True).first
        b.scroll_into_view_if_needed(timeout=8000)
        b.click(timeout=10000, force=True)
        print("click VER ok")
    except Exception as e:
        print("click VER fallo", repr(e)[:300])
        try:
            pg.get_by_text("Más apuestas", exact=True).first.click(
                timeout=8000, force=True)
            print("click Mas apuestas ok")
        except Exception as e2:
            print("click Mas apuestas fallo", repr(e2)[:300])
    pg.wait_for_timeout(15000)
    print("\nURL tras pulsar:", pg.url)
    print("titulo:", pg.title()[:100])
    t = pg.inner_text("body")
    print("longitud texto:", len(t))
    print("\n--- Lineas con palabras clave ---")
    n = 0
    for ln in t.split("\n"):
        if CLAVES.search(ln) and n < 60:
            n += 1
            print(" ", ln[:120])
    j = t.find("Más apuestas")
    k = t.find("Partidos")
    print("\n--- TEXTO del partido (3500 car.) ---")
    print(t[1000:4500].replace("\n", " | "))
    br.close()
print("fin")
