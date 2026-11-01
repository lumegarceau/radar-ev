import os
import json
import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def pulsar(page, selector, timeout=3000):
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
    for _ in range(5):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        btn_mas = page.locator("button:has-text('Seguir buscando'), button:has-text('Cargar más')").first
        if await btn_mas.is_visible(timeout=2000):
            await btn_mas.click()
            await page.wait_for_timeout(2500)
        else:
            break

async def extraer_tarjetas(page, tipo):
    candidatos = []
    bloques = await page.locator("div:has-text('ACIERTOS')").all()
    
    for b in bloques:
        try:
            texto = await b.inner_text()
            m = re.search(r"(\d+)/20\s*ACIERTOS", texto)
            if not m:
                m = re.search(r"(\d+)/20", texto)
            
            if m:
                aciertos = int(m.group(1))
                if aciertos >= 14:
                    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
                    comp = lineas[0] if len(lineas) > 0 else "Fútbol"
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
                    candidatos.append({
                        "comp": comp,
                        "partido": partido,
                        "hora": "Hoy",
                        "nombre": nombre,
                        "equipo": equipo,
                        "mercado": mercado,
                        "casa": "WINAMAX",
                        "cuota": 1.85,
                        "l20": f"{aciertos}/20",
                        "pct": f"{int(prob * 100)}%",
                        "pFinal": prob,
                        "justa": round(1 / prob, 2),
                        "ev": round(((1.85 * prob) - 1), 2)
                    })
        except Exception:
            continue
    return candidatos

async def run():
    todos = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("1. Accediendo a ValueStats...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        await pulsar(page, "button:has-text('Aceptar'), button:has-text('Aceptar todas')")

        btn_iniciar = page.locator("button:has-text('Iniciar sesión'), a:has-text('Iniciar sesión'), span:has-text('Iniciar sesión')").first
        if await btn_iniciar.is_visible(timeout=3000):
            print("2. Abriendo modal de login...")
            await btn_iniciar.click()
            await page.wait_for_timeout(2000)

        inp_email = page.locator("input[type='email'], input[name='email'], input[placeholder*='correo' i], input[placeholder*='email' i]").first
        if await inp_email.is_visible(timeout=3000):
            print("3. Introduciendo credenciales...")
            await inp_email.fill(USER)
            await page.locator("input[type='password'], input[name='password']").first.fill(PASS)
            await pulsar(page, "button[type='submit'], button:has-text('Iniciar sesión'), button:has-text('Entrar')")
            await page.wait_for_timeout(5000)

        if "radar-props" not in page.url:
            await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(4000)

        # 1. JUGADORES
        print("4. Buscando en JUGADORES...")
        await pulsar(page, "button:has-text('Jugadores'), [role='button']:has-text('Jugadores')")
        await page.wait_for_timeout(1500)
        await pulsar(page, "button:has-text('L20'), label:has-text('L20')")
        await pulsar(page, "button:has-text('Todas'), label:has-text('Todas')")

        await pulsar(page, "button:has-text('Buscar candidatos')")
        await page.wait_for_timeout(6000)
        await scroll_y_seguir(page)
        jugs = await extraer_tarjetas(page, "Jugador")
        print(f"Jugadores encontrados: {len(jugs)}")
        todos.extend(jugs)

        # 2. EQUIPOS
        print("5. Buscando en EQUIPOS...")
        await pulsar(page, "button:has-text('Equipos'), [role='button']:has-text('Equipos')")
        await page.wait_for_timeout(1500)

        mercados = ["Córners del equipo", "Tiros del equipo", "Tiros a puerta del equipo", "Faltas del equipo", "Tarjetas del equipo"]
        for m in mercados:
            print(f"Revisando: {m}...")
            try:
                sel = page.locator("div:has-text('Mercado')").locator("..").locator("div, select").first
                await sel.click()
                await page.wait_for_timeout(1000)
                await pulsar(page, f"li:has-text('{m}'), div:has-text('{m}'), [role='option']:has-text('{m}')")
            except Exception:
                pass

            await pulsar(page, "button:has-text('Todas'), label:has-text('Todas')")
            await pulsar(page, "button:has-text('L20'), label:has-text('L20')")
            await pulsar(page, "button:has-text('Buscar candidatos')")
            await page.wait_for_timeout(5000)
            await scroll_y_seguir(page)
            eqs =
