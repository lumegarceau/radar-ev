import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 3000})
    pg = ctx.new_page()
    xhr = []
    pg.on("response", lambda r: xhr.append((r.status, r.request.resource_type, r.url[:140])) if r.request.resource_type in ("xhr", "fetch") else None)
    pg.goto("https://apuestas.juegging.es/esp/Sport", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(12000)
    for txt in ("Aceptar", "Aceptar todas", "ACEPTAR"):
        try:
            pg.get_by_text(txt, exact=True).first.click(timeout=1500)
            break
        except Exception:
            pass
    print("== A. Partido: REPUBLICA CHECA VS. ESPAÑA")
    ok = False
    for pat in (r"REP[ÚU]BLICA CHECA VS\. ESPAÑA", r"\(\+ ?207\)", r"CHECA"):
        try:
            pg.get_by_text(re.compile(pat, re.I)).first.click(timeout=5000)
            ok = True
            break
        except Exception as e:
            print("   no pulsa", pat, repr(e)[:60])
    pg.wait_for_timeout(12000)
    print("url:", pg.url, "| pulsado:", ok)
    t = limpio(pg)
    print("longitud:", len(t))
    print("texto:", t[:1800])
    print("\n== B. Pestañas / categorias visibles")
    for w in ("Jugadores", "JUGADORES", "Tiros", "Props", "Estadísticas", "Córners", "Corners", "Más mercados"):
        print("  ", w, "->", w in t)
    print("\n== C. Intento de abrir Jugadores")
    for pat in (r"^Jugadores?$", r"Jugador", r"Tiros"):
        try:
            pg.get_by_text(re.compile(pat, re.I)).first.click(timeout=4000)
            pg.wait_for_timeout(6000)
            t2 = limpio(pg)
            print("pulsado", pat, "| longitud:", len(t2))
            i = t2.lower().find("jugador")
            print("texto desde 'jugador':", t2[max(i, 0):max(i, 0) + 1500])
            break
        except Exception as e:
            print("   no pulsa", pat, repr(e)[:60])
    print("\n== D. XHR (estado, tipo, url)")
    vistos = set()
    for s, ty, u in xhr:
        k = u.split("?")[0]
        if k in vistos:
            continue
        vistos.add(k)
        print("  ", s, ty, u)
        if len(vistos) > 40:
            break
    br.close()
