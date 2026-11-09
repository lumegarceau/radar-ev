import re, time
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    t = re.sub(r"\s+", " ", pg.inner_text("body"))
    k = t.find("Volver al inicio")
    return t[:k] if k > 0 else t


def prueba(nom, url):
    print("\n=====", nom, url)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 3000})
        pg = ctx.new_page()
        t0 = time.time()
        try:
            pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(5000)
            try:
                pg.get_by_text("Aceptar", exact=True).first.click(timeout=2500)
            except Exception:
                pass
            pg.wait_for_timeout(9000)
            pg.get_by_text("Francia", exact=True).first.click(timeout=6000)
            pg.wait_for_timeout(9000)
            pg.get_by_text(re.compile(r"^Jugadores\b"), exact=False).first.click(timeout=4000)
            pg.wait_for_timeout(4000)
            pg.locator("xpath=//*[normalize-space(text())='Mercado']").first.click(timeout=3000)
            pg.wait_for_timeout(4000)
            print("segundos hasta ver mercados:", round(time.time() - t0))
            # tiempo total de la vista y titulos de mercados
            t = limpio(pg)
            print("longitud vista Mercado:", len(t))
            tit = re.findall(r"((?:[A-ZÁÉÍÓÚÑ][\wáéíóúñ/]*\s){1,6}?(?:Totales|Cometidas|Recibidas|Paradas|Tarjetas?))\s(?=[A-ZÁÉÍÓÚÑ][a-zñáéíóú]+ [A-Z])", t)
            print("titulos detectados:", sorted(set(tit))[:40])
            for pal in ["Falta", "Tarjeta", "Entrada", "Parada", "Fuera de Juego", "Regate"]:
                print("  contiene", pal, "->", t.count(pal))
            # pulsar MOSTRAR TODO del primer mercado de tiros a puerta
            antes = len(t)
            try:
                bt = pg.get_by_text("MOSTRAR TODO", exact=True)
                print("botones MOSTRAR TODO:", bt.count())
                bt.nth(1).click(timeout=3000)
                pg.wait_for_timeout(4000)
                t2 = limpio(pg)
                print("tras MOSTRAR TODO (2o):", antes, "->", len(t2))
                i = t2.find("Tiros a Puerta Totales")
                print(t2[i:i + 2600])
            except Exception as e:
                print("MOSTRAR TODO falla:", repr(e)[:80])
            # ultimo trozo: otros mercados al final de la vista
            print("\nFINAL de la vista:", t[-1800:])
        except Exception as e:
            print("FALLO", repr(e)[:200])
        br.close()


prueba("Sportium", "https://www.sportium.es/apuestas/sports/soccer/competitions/46767/matches")
prueba("Marca Apuestas", "https://www.marcaapuestas.es/apuestas/sports/soccer/competitions/556801/matches")
print("\nfin")
