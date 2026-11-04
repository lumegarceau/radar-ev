import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es"
LIGA = BASE + "/es/es/sports/grp/soccer/spain/la-liga"
EVT = BASE + "/es/es/sports/evt/17397080"

with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 1800})
    pg = ctx.new_page()
    pg.goto(LIGA, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(10000)
    try:
        pg.locator("#onetrust-accept-btn-handler").first.click(timeout=4000)
    except Exception:
        pass
    pg.wait_for_timeout(2000)
    html = pg.content()
    print("=== IDs de partido en el HTML de la liga ===")
    ids = []
    for m in re.finditer(r"(?<!\d)(173\d{5}|174\d{5})(?!\d)", html):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    print(len(ids), ids[:30])
    i = html.find(ids[0]) if ids else -1
    if i >= 0:
        print("\nContexto del primero:")
        print(html[max(0, i - 400):i + 300])
    print("\n=== Enlaces con evt ===")
    hs = pg.eval_on_selector_all(
        "[href],[data-event-id],[data-id]",
        "e=>e.map(x=>[x.getAttribute('href'),x.getAttribute("
        "'data-event-id'),x.getAttribute('data-id')])")
    n = 0
    for h in hs:
        if any(h) and n < 20 and any(
                x and re.search(r"\d{7,}|evt", x) for x in h):
            n += 1
            print(h)

    print("\n\n=== PARTIDO ===")
    pg.goto(EVT, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(12000)
    print(pg.title()[:80])
    for nombre in ("Córners", "Tarjetas", "Tiros", "Faltas", "Remates"):
        try:
            loc = pg.get_by_text(nombre, exact=False)
            print("\n##", nombre, "coincidencias:", loc.count())
            loc.first.click(timeout=8000, force=True)
            pg.wait_for_timeout(5000)
            t = pg.inner_text("body")
            j = t.find(nombre)
            print(t[max(0, j - 100):j + 900].replace("\n", " | "))
        except Exception as e:
            print(nombre, "fallo", repr(e)[:150])
    t = pg.inner_text("body")
    print("\n=== LISTA de mercados visibles (lineas cortas) ===")
    for ln in t.split("\n")[:140]:
        s = ln.strip()
        if s and len(s) < 60:
            print(" ", s)
    br.close()
print("fin")
