import os
import json
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def pulsar(page, selector, timeout=4000):
    try:
        loc = page.locator(selector).first
        if await loc.is_visible(timeout=timeout):
            await loc.click()
            await page.wait_for_timeout(1000)
            return True
    except Exception:
        pass
    return False

async def scroll_y_seguir(page):
    """Baja por la página y pulsa 'Seguir buscando' si aparece"""
    for _ in range(6):
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
    bloques = await page.locator("div:has-text('ACIERTOS')").all()
    
    for bloque in bloques:
        try:
            texto = await bloque.inner_text()
            match = re.search(r"(\d+)/20\s*ACIERTOS", texto)
            if not match:
                match = re.search(r"(\d+)/20", texto)
            
            if match:
                aciertos = int(match.group(1))
                if aciertos >= 14: # 70%+ histórico
                    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
                    
                    competicion = lineas[0] if len(lineas) > 0 else "Fútbol"
                    nombre = lineas[2] if len(lineas) > 2 else tipo
                    equipo = lineas[3] if len(lineas) > 3 else ""
                    partido = "Partido del día"
                    mercado = "Línea L20"
                    
                    for l in lineas:
                        if " vs " in l or "PARTIDO" in l:
                            partido = l.replace("PARTIDO", "").strip()
                        elif any(k in l.lower() for k in ["más de", "menos de", "tiros", "corners", "córners", "faltas", "tarjetas"]):
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
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("1. Entrando a ValueStats...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        # Cookies si aparecen
        await pulsar(page, "button:has-text('Aceptar'), button:has-text('Aceptar todas')")

        # Comprobar si hay botón de Iniciar sesión y pulsarlo
        print("2. Comprobando sesión...")
        btn_iniciar = page.locator("button:has-text('Iniciar sesión'), a:has-text('Iniciar sesión'), span:has-text('Iniciar sesión')").first
        if await btn_iniciar.is_visible(timeout=3000):
            print("Pulsando botón 'Iniciar sesión' para abrir el modal...")
            await btn_iniciar.click()
            await page.wait_for_timeout(2000)

        # Rellenar credenciales si el modal está abierto
        input_email = page.locator("input[type='email'], input[name='email'], input[placeholder*='correo' i], input[placeholder*='email' i]").first
        if await input_email.is_visible(timeout=3000):
            print("Introduciendo usuario y contraseña...")
            await input_email.fill(USER)
            await page.locator("input[type='password'], input[name='password']").first.fill(PASS)
            await pulsar(page, "button[type='submit'], button:has-text('Iniciar sesión'), button:has-text('Entrar')")
            await page.wait_for_timeout(5000)

        # Asegurar que estamos en el radar de props
        if "radar-props" not in page.url:
            await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)

        # ==========================================
        # 1. BÚSQUEDA JUGADORES
        # ==========================================
        print("3. Conf
