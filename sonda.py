import re, time
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SITIOS = [
    ("Betfair ES", "https://apuestas.betfair.es/"),
    ("Betfair ES futbol", "https://apuestas.betfair.es/sport/football"),
    ("Kirolbet", "https://www.kirolbet.es/"),
    ("Retabet", "https://www.retabet.es/"),
    ("Juegging", "https://www.juegging.es/"),
]


def limpio(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


with sync_playwright() as pw:
    br = pw.chromium.launch()
    for nom, url in SITIOS:
        print("\n=====", nom, url)
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 2500})
        pg = ctx.new_page()
        st = []
        pg.on("response", lambda r, st=st: st.append(r.status) if r.url.rstrip("/").count("/") <= 3 else None)
        try:
            r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("estado:", r.status if r else None, "url final:", pg.url)
            pg.wait_for_timeout(9000)
            for txt in ("Aceptar", "Aceptar todas", "Aceptar todo", "ACEPTAR", "Acepto"):
                try:
                    pg.get_by_text(txt, exact=True).first.click(timeout=1500)
                    break
                except Exception:
                    pass
            pg.wait_for_timeout(6000)
            print("titulo:", pg.title())
            t = limpio(pg)
            print("longitud texto:", len(t))
            print("texto:", t[:600])
            bloq = [w for w in ("not available in your", "no disponible", "access denied", "forbidden",
                                "blocked", "restringido", "geolocal", "captcha", "cloudflare", "403") if w in t.lower()]
            print("posible bloqueo:", bloq)
            links = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')).filter(h=>/futbol|football|soccer|nations/i.test(h)).slice(0,15)")
            print("enlaces de futbol:", links)
        except Exception as e:
            print("falla:", repr(e)[:200])
        ctx.close()
    br.close()
