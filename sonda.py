import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2500})
    pg = ctx.new_page()
    pg.goto("https://www.juegging.es/", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(8000)
    for txt in ("Aceptar", "Aceptar todas", "Aceptar todo"):
        try:
            pg.get_by_text(txt, exact=True).first.click(timeout=1500)
            break
        except Exception:
            pass
    links = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>(a.innerText||'').trim().slice(0,40)+' -> '+a.href).filter(x=>/apuest|deport|sport|bet/i.test(x))")
    print("enlaces:")
    for l in links[:40]:
        print("  ", l)
    for pat in (r"^APUESTAS DEPORTIVAS$", r"^Ir a Apuestas$"):
        try:
            with ctx.expect_page(timeout=8000) as nueva:
                pg.get_by_text(re.compile(pat, re.I)).first.click(timeout=4000)
            p2 = nueva.value
        except Exception:
            p2 = pg
        p2.wait_for_timeout(15000)
        print("\nTras pulsar", pat, "->", p2.url)
        print("titulo:", p2.title())
        print("texto:", limpio(p2)[:800])
        break
    br.close()
