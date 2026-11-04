from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
EVT = "https://betway.es/es/es/sports/evt/17397080"
PESTANAS = ["corners", "players", "other", "goals", "half"]
JS_CLICK = (
    "p=>{const e=document.querySelector('li[data-testid=\"'+p+'\"]');"
    "if(!e)return 'no existe';e.click();return 'click por JS'}")
JS_SEL = (
    "()=>Array.from(document.querySelectorAll('li[role=tab]'))"
    ".map(e=>e.dataset.testid+':'+e.getAttribute('aria-selected'))"
    ".join(' ')")


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
                         viewport={"width": 1366, "height": 2400})
    pg = ctx.new_page()
    pg.goto(EVT, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(12000)
    try:
        pg.get_by_text("Aceptar Todo", exact=True).first.click(timeout=8000)
        print("cookies: Aceptar Todo pulsado")
    except Exception as e:
        print("cookies fallo", repr(e)[:150])
    pg.wait_for_timeout(3000)
    for p in PESTANAS:
        print("\n" + "=" * 50)
        print("PESTANA:", p)
        try:
            print(pg.evaluate(JS_CLICK, p))
            pg.wait_for_timeout(6000)
            print("pestanas:", pg.evaluate
