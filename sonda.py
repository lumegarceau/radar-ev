import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
URL = "https://apuestas.juegging.es/esp/Sport/Evento/12067249"


def limpio(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 4000})
    pg = ctx.new_page()
    pg.goto(URL, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    print("url:", pg.url, "| titulo:", pg.title())
    t = limpio(pg)
    print("longitud:", len(t))
    i = t.find("Checa")
    print("== A. Texto desde el partido (3500 car.)")
    print(t[max(i - 100, 0):max(i - 100, 0) + 3500])
    print("\n== B. Palabras clave")
    for w in ("Jugador", "Tiros", "Córners", "Faltas", "Tarjetas", "Entradas", "Paradas", "Goleador", "Disparos"):
        print("  ", w, "->", w.lower() in t.lower())
    print("\n== C. Pestañas / cabeceras de mercado")
    cab = pg.evaluate("""()=>Array.from(document.querySelectorAll('h2,h3,h4,[class*=tab],[class*=Tab],[class*=cabecera],[class*=mercado],[class*=grupo]'))
        .map(e=>(e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,60)).filter(x=>x&&x.length<60)""")
    vistos = []
    for c in cab:
        if c not in vistos:
            vistos.append(c)
    print(vistos[:80])
    br.close()
