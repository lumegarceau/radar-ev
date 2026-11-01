import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def run():
    candidatos = []
    
    async with async_playwright() as p:
        # Lanzamos un navegador invisible
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print("1. Entrando a ValueStats...")
        await page.goto("https://valuestats.com/login", wait_until="networkidle", timeout=60000)

        # Si pide aceptar cookies, pulsamos 'Aceptar'
        try:
            btn_cookie = page.locator("button:has-text('Aceptar'), button:has-text('Aceptar todas')").first
            if await btn_cookie.is_visible(timeout=3000):
                await btn_cookie.click()
        except Exception:
            pass

        print("2. Iniciando sesión...")
        await page.fill("input[type='email'], input[name='email'], input[name='username']", USER)
        await page.fill("input[type='password'], input[name='password']", PASS)
        await page.click("button[type='submit'], button:has-text('Iniciar sesión'), button:has-text('Entrar')")
        
        await page.wait_for_timeout(4000)

        # Vamos directo al Radar de Props
        print("3. Navegando al Radar de Props...")
        await page.goto("https://valuestats.com/radar-props", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

        # Seleccionar histórico L20
        try:
            print("4. Seleccionando L20...")
            l20_btn = page.locator("button:has-text('L20'), [role='button']:has-text('L20'), label:has-text('L20')").first
            if await l20_btn.is_visible(timeout=5000):
                await l20_btn.click()
                await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Aviso al seleccionar L20: {e}")

        # Recorremos tanto la pestaña 'Jugadores' como 'Equipos'
        for vista in ["Jugadores", "Equipos"]:
            try:
                print(f"5. Extrayendo datos de: {vista}...")
                tab = page.locator(f"button:has-text('{vista}'), a:has-text('{vista}')").first
                if await tab.is_visible(timeout=3000):
                    await tab.click()
                    await page.wait_for_timeout(3000)

                # Extraer las filas o tarjetas que cumplan >= 14 de 20 (70%)
                filas = await page.locator("tr, div[class*='card'], div[class*='row']").all()
                for f in filas:
                    texto = await f.inner_text()
                    # Buscamos patrones de L20 con al menos 14 aciertos (14/20 hasta 20/20)
                    for n in range(14, 21):
                        patron = f"{n}/20"
                        if patron in texto:
                            lineas = [l.strip() for l in texto.split("\n") if l.strip()]
                            if len(lineas) >= 3:
                                candidatos.append({
                                    "comp": "Fútbol",
                                    "partido": lineas[0] if len(lineas) > 0 else "Partido",
                                    "hora": "Hoy",
                                    "nombre": lineas[1] if len(lineas) > 1 else vista,
                                    "equipo": vista,
                                    "mercado": lineas[2] if len(lineas) > 2 else "Línea L20",
                                    "casa": "WINAMAX",
                                    "cuota": 1.85,
                                    "l20": patron,
                                    "pct": f"{int((n/20)*100)}%",
                                    "pFinal": n / 20.0,
                                    "justa": round(1 / (n / 20.0), 2),
                                    "ev": round(((1.85 * (n / 20.0)) - 1), 2)
                                })
                            break
            except Exception as e:
                print(f"Error procesando {vista}: {e}")

        await browser.close()

    # Guardar en el archivo radar-data.json
    ahora = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    resultado = {
        "updated_at": ahora,
        "days": [
            {
                "candidatos": candidatos
            }
        ]
    }

    with open("radar-data.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"¡Éxito! Se han guardado {len(candidatos)} candidatos con 14/20 o más.")

if __name__ == "__main__":
    asyncio.run(run())
