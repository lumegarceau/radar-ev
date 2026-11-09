import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


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
            # abrir el partido Italia - Francia
            try:
                pg.get_by_text("Francia", exact=True).first.click(timeout=6000)
            except Exception as e:
                print("no pude pulsar el partido:", repr(e)[:100])
                return
            pg.wait_for_timeout(14000)
            print("URL partido:", pg.url)
            t = limpio(pg)
            i = t.find("Francia")
            print("texto partido:", len(t))
            print(t[max(0, i - 100):i + 3500])
            # pestanas / categorias de mercados
            etiquetas = pg.evaluate("""()=>Array.from(document.querySelectorAll('[role=tab],button,a'))
                .map(e=>(e.innerText||'').trim()).filter(s=>s&&s.length<28)""")
            print("botones/pestanas:", sorted(set(etiquetas))[:80])
            for pal in ["Corners", "Córners", "Tiros", "Jugadores", "Tarjetas", "Todos", "Goleador", "Especiales"]:
                try:
                    pg.get_by_text(pal, exact=False).first.click(timeout=2500)
                    pg.wait_for_timeout(6000)
                    t2 = limpio(pg)
                    j = t2.find(pal)
                    print("\n--- tras pulsar", pal, "| texto", len(t2))
                    print(t2[max(0, j - 50):j + 1500])
                except Exception:
                    print("\n(sin pestana", pal + ")")
        except Exception as e:
            print("FALLO", repr(e)[:200])
        br.close()


prueba("Sportium", "https://www.sportium.es/apuestas/sports/soccer/competitions/46767/matches")
prueba("Marca Apuestas", "https://www.marcaapuestas.es/apuestas/sports/soccer/competitions/556801/matches")
print("\nfin")
