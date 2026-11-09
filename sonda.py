import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    t = re.sub(r"\s+", " ", pg.inner_text("body"))
    k = t.find("Volver al inicio")
    return t[:k] if k > 0 else t


def trozo(t, ini, n=1800):
    i = t.find(ini)
    return t[max(0, i - 60):i + n] if i >= 0 else t[:n]


def prueba(nom, url):
    print("\n=====", nom, url)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 3000})
        pg = ctx.new_page()
        try:
            pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            try:
                pg.get_by_text("Aceptar", exact=True).first.click(timeout=2500)
            except Exception:
                pass
            pg.wait_for_timeout(12000)
            pg.get_by_text("Francia", exact=True).first.click(timeout=6000)
            pg.wait_for_timeout(12000)
            print("URL partido:", pg.url)
            # pestanas con numero: Equipos / Especiales / Jugadores / Minutos
            for pal in ["Equipos", "Especiales"]:
                try:
                    pg.get_by_text(re.compile(r"^" + pal + r"\b"), exact=False).first.click(timeout=3000)
                    pg.wait_for_timeout(5000)
                    print("\n--- pestana", pal)
                    print(trozo(limpio(pg), "Mercados", 1600))
                except Exception as e:
                    print("\n(sin pestana", pal + ")", repr(e)[:60])
            pg.get_by_text(re.compile(r"^Jugadores\b"), exact=False).first.click(timeout=4000)
            pg.wait_for_timeout(5000)
            # abrir el desplegable Mercado
            abierto = False
            for sel in ["text=Mercado", "[class*=select]", "select"]:
                try:
                    pg.locator(sel).first.click(timeout=3000)
                    abierto = True
                    break
                except Exception:
                    pass
            pg.wait_for_timeout(2500)
            print("\n--- desplegable abierto:", abierto)
            ops = pg.evaluate("""()=>Array.from(document.querySelectorAll('option,[role=option],li'))
               .map(e=>(e.innerText||e.textContent||'').trim()).filter(s=>s&&s.length<45)""")
            print("opciones:", ops[:70])
            for pal in ["Remates a Puerta", "Tiros a Puerta", "Remates", "Tiros", "Faltas"]:
                try:
                    pg.get_by_text(pal, exact=False).first.click(timeout=2500)
                    pg.wait_for_timeout(5000)
                    t = limpio(pg)
                    print("\n--- elegido:", pal, "| texto", len(t))
                    print(trozo(t, "Mercado", 1800))
                    # elegir primer jugador
                    try:
                        pg.get_by_text("Kylian Mbappe", exact=False).first.click(timeout=3000)
                        pg.wait_for_timeout(5000)
                        t = limpio(pg)
                        print("--- tras elegir Mbappe:")
                        print(trozo(t, "Mbappe", 1500))
                    except Exception as e:
                        print("no pude elegir jugador", repr(e)[:60])
                    break
                except Exception:
                    pass
        except Exception as e:
            print("FALLO", repr(e)[:200])
        br.close()


prueba("Sportium", "https://www.sportium.es/apuestas/sports/soccer/competitions/46767/matches")
prueba("Marca Apuestas", "https://www.marcaapuestas.es/apuestas/sports/soccer/competitions/556801/matches")
print("\nfin")
