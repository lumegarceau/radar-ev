"""Sonda de Betsson: que carga, desde donde y que datos de cuotas circulan."""
import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
URLS = [
    ("Betsson 1", "https://www.betsson.es/"),
    ("Betsson 2", "https://www.betsson.es/apuestas-deportivas"),
    ("Betsson 3", "https://www.betsson.es/es/apuestas-deportivas/futbol"),
    ("Betsson 4", "https://sports.betsson.es/"),
    ("Betsson 5", "https://sportsbook.betsson.es/"),
    ("Betsson 6", "https://apuestas.betsson.es/"),
]
CLAVES = ("odds", "price", "decimal", "cuota", "selection", "outcome", "market", "betOffer", "events")


def sonda(br, nombre, url):
    print("\n=====", nombre, url, flush=True)
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2500})
    pg = ctx.new_page()
    vistos = []

    def resp(r):
        try:
            ct = (r.headers.get("content-type") or "").lower()
            if "json" not in ct:
                return
            cuerpo = r.text()
            n = len(cuerpo)
            k = [c for c in CLAVES if c.lower() in cuerpo.lower()[:400000]]
            vistos.append((r.status, n, r.url[:150], k[:6]))
        except Exception:
            pass

    pg.on("response", resp)
    try:
        r = pg.goto(url, timeout=45000, wait_until="domcontentloaded")
        print("estado:", r.status if r else None, "| url final:", pg.url[:150])
    except Exception as e:
        print("no carga:", repr(e)[:150])
        ctx.close()
        return
    pg.wait_for_timeout(15000)
    try:
        t = re.sub(r"\s+", " ", pg.inner_text("body"))
        print("titulo:", pg.title()[:100], "| texto:", len(t), "caracteres")
        print("texto inicio:", t[:350])
        bajo = t.lower()
        for m in ("access denied", "forbidden", "not available in your", "no disponible en tu", "bloqueado", "captcha", "pardon", "geo"):
            if m in bajo:
                print("  aviso de bloqueo?:", m)
        enl = pg.evaluate("""()=>Array.from(document.querySelectorAll('a')).map(a=>a.href).filter(h=>/futbol|football|soccer|deporte|sport/i.test(h)).slice(0,15)""")
        print("enlaces de deporte:", enl)
    except Exception as e:
        print("lectura falla:", repr(e)[:100])
    vistos.sort(key=lambda x: -x[1])
    print("respuestas JSON:", len(vistos))
    for v in vistos[:15]:
        print("  ", v)
    ctx.close()


with sync_playwright() as pw:
    br = pw.chromium.launch(args=["--disable-blink-features=AutomationControlled"])
    for n, u in URLS:
        try:
            sonda(br, n, u)
        except Exception as e:
            print(n, "falla", repr(e)[:100])
    br.close()
