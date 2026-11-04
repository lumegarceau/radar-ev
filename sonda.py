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
    pg.wait_for_timeout(12000)
    print("URL liga:", pg.url)
    for etq in ("VER", "Más apuestas"):
        n = pg.get_by_text(etq, exact=True).count()
        print("botones", etq, ":", n)
    try:
        pg.get_by_text("VER", exact=True).first.click(timeout=15000)
    except Exception as e:
        print("click VER fallo", repr(e)[:150])
        try:
            pg.get_by_text("Más apuestas", exact=True).first.click(
                timeout=15000)
        except Exception as e2:
            print("click Mas apuestas fallo", repr(e2)[:150])
    pg.wait_for_timeout(15000)
    print("\nURL tras pulsar:", pg.url)
    print("titulo:", pg.title()[:100])
    t = pg.inner_text("body")
    print("longitud texto:", len(t))
    i = t.find("Partidos")
    print("\n--- TEXTO (desde el contenido, 4500 car.) ---")
    print(t[1200:5700].replace("\n", " | "))
    print("\n--- Lineas con palabras clave ---")
    n = 0
    for ln in t.split("\n"):
        if CLAVES.search(ln) and n < 40:
            n += 1
            print(" ", ln[:120])
    pg.screenshot(path="betway.png", full_page=False)
    br.close()
print("fin")
