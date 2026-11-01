import os
import json
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def pulsar_si_existe(page, selector, timeout=3000):
    try:
        loc = page.locator(selector).first
        if await loc.is_visible(timeout=timeout):
            await loc.click()
            await page.wait_for_timeout(1000)
            return True
    except Exception:
        pass
    return False

async def scroll_y_seguir_buscando(page):
    """Pulsa el botón de seguir buscando hasta que no salgan más resultados"""
    for _ in range(8): # Intentar hasta 8 veces para traer todos los datos
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        btn_mas = page.locator("button:has-text('Seguir buscando'), button:has-text('Cargar más'), [role='button']:has-text('Seguir')").first
        if await btn_mas.is_visible(timeout=2000):
            print("Pulsando 'Seguir buscando'...")
            await btn_mas.click()
            await page.wait_for_timeout(3000)
        else:
            break

async def extraer_tarjetas(page, tipo):
    candidatos = []
    # Buscamos todas las tarjetas o bloques de resultados
    bloques = await page.locator("div:has-text('ACIERTOS')").all()
    
    for bloque in bloques:
        try:
            texto = await bloque.inner_text()
            # Buscar el patrón "14/20 ACIERTOS" hasta "20/20 ACIERTOS"
            match = re.search(r"(\d+)/20\s*ACIERTOS", texto)
            if not match:
                match = re.search(r"(\d+)/20", texto)
            
            if match:
                aciertos = int(match.group(1))
                if aciertos >= 14: # Filtro del 70%+ (14 de 20 o más)
                    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
                    
                    # Extraer los datos de la tarjeta
                    competicion = lineas[0] if len(lineas) > 0 else "Fútbol"
                    nombre = lineas[2] if len(lineas) > 2 else tipo
                    equipo = lineas[3] if len(lineas) > 3 else ""
                    
                    partido = "Partido del día"
                    mercado = "Línea L20"
                    
                    for l in lineas:
                        if " vs " in l or "PARTIDO" in l:
                            partido = l.replace("PARTIDO", "").strip()
                        elif "Más de" in l or "Menos de" in l or "tiros" in l or "corners" in l or "faltas" in l or "tarjetas" in l:
                            mercado = l.strip()

                    prob = aciertos / 20.0
                    cuota_justa = round(1 / prob, 2)
                    cuota_estimada = 1.85

                    candidatos.append({
                        "comp": competicion,
                        "partido": partido,
                        "hora": "Hoy",
                        "nombre": nombre,
                        "equipo": equipo,
                        "mercado": mercado,
                        "casa": "WINAMAX",
                        "cuota": cuota_estimada,
                        "l20": f"{aciertos}/20",
                        "pct": f"{int(prob * 100)}%",
                        "pFinal": prob,
                        "justa": cuota_justa,
                        "ev": round(((cuota_estimada * prob) - 1), 2)
                    })
        except Exception:
            continue
            
    return candidatos

async def run():
    todos_candidatos = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Pantalla grande para ver todos los menús sin problemas
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("1. Iniciando sesión en ValueStats...")
        await page.goto("https://valuestats.com/login", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        # Cookies
        await pulsar_si_existe(page, "button:has-text('Aceptar')")

        # Login
        await page.fill("input[type='email'], input[name='email'], input[name='username']", USER)
        await page.fill("input[type='password'], input[name='password']", PASS)
        await page.click("button[type='submit'], button:has-text('Iniciar sesión'), button:has-text('Entrar')")
        await page.wait_for_timeout(5000)

        print("2. Entrando al Radar de Props...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        # ==========================================
        # 1. BÚSQUEDA EN JUGADORES
        # ==========================================
        print("3. Configurando pestaña: JUGADORES...")
        await pulsar_si_existe(page, "button:has-text('Jugadores'), [role='button']:has-text('Jugadores')")
        await page.wait_for_timeout(2000)

        # Histórico L20 y Condición Todas
        await pulsar_si_existe(page, "button:has-text('L20'), label:has-text('L20')")
        await pulsar_si_existe(page, "button:has-text('Todas'), label:has-text('Todas')")

        # Rendimiento 70%+
        try:
            rend = page.locator("div:has-text('Rendimiento'), div:has-text('Frecuencia')").first
            if await rend.is_visible(timeout=2000):
                await rend.click()
                await page.wait_for_timeout(1000)
                await pulsar_si_existe(page, "div:has-text('70%+'), li:has-text('70%+'), option:has-text('70%+'), span:has-text('70%+'), [role='option']:has-text('70%')")
        except Exception:
            pass

        # Pulsar BUSCAR CANDIDATOS
        print("Buscando candidatos de Jugadores...")
        await pulsar_si_existe(page, "button:has-text('Buscar candidatos')")
        await page.wait_for_timeout(6000)
        
        await scroll_y_seguir_buscando(page)
        encontrados_jug = await extraer_tarjetas(page, "Jugador")
        print(f"-> Jugadores encontrados: {len(encontrados_jug)}")
        todos_candidatos.extend(encontrados_jug)

        # ==========================================
        # 2. BÚSQUEDA EN EQUIPOS
        # ==========================================
        print("4. Configurando pestaña: EQUIPOS...")
        await pulsar_si_existe(page, "button:has-text('Equipos'), [role='button']:has-text('Equipos')")
        await page.wait_for_timeout(2000)

        mercados_equipo = [
            "Córners del equipo",
            "Tiros del equipo",
            "Tiros a puerta del equipo",
            "Faltas del equipo",
            "Tarjetas del equipo"
        ]

        for merc in mercados_equipo:
            print(f"Analizando mercado de equipos: {merc}...")
            # Seleccionar mercado
            try:
                sel_merc = page.locator("div:has-text('Mercado')").locator("..").locator("div, select").first
                await sel_merc.click()
                await page.wait_for_timeout(1000)
                await pulsar_si_existe(page, f"li:has-text('{merc}'), div:has-text('{merc}'), [role='option']:has-text('{merc}')")
            except Exception:
                pass

            # Línea Todas, Histórico L20, Condición Todas
            await pulsar_si_existe(page, "button:has-text('Todas'), label:has-text('Todas')")
            await pulsar_si_existe(page, "button:has-text('L20'), label:has-text('L20')")

            # Buscar candidatos
            await pulsar_si_existe(page, "button:has-text('Buscar candidatos')")
            await page.wait_for_timeout(5000)
            
            await scroll_y_seguir_buscando(page)
            encontrados_eq = await extraer_tarjetas(page, "Equipo")
            print(f"-> {merc}: {len(encontrados_eq)} candidatos.")
            todos_candidatos.extend(encontrados_eq)

        await browser.close()

    # Eliminar duplicados si los hubiera
    unicos = []
    vistos = set()
    for c in todos_candidatos:
        clave = f"{c['nombre']}_{c['mercado']}_{c['partido']}"
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(c)

    # Guardar en radar-data.json
    ahora = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    resultado = {
        "updated_at": ahora,
        "days": [
            {
                "candidatos": unicos
            }
        ]
    }

    with open("radar-data.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print(f"¡TERMINADO! Se guardaron {len(unicos)} sucesos con 14/20 o más en radar-data.json.")

if __name__ == "__main__":
    asyncio.run(run())
