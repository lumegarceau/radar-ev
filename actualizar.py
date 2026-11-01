import os, json, asyncio, re
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def click_txt(page, txt, exact=False):
    try:
        loc = page.get_by_text(txt, exact=exact).first
        if await loc.is_visible(timeout=3000):
            await loc.click()
            print(f"  [OK] {txt}")
            await page.wait_for_timeout(1000)
            return True
    except: pass
    return False

async def get_cards(page, tipo):
    cards = []
    # Cargar más si hay botón
    for _ in range(6):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        btn = page.get_by_text("Seguir buscando").first
        if await btn.is_visible(timeout=1500):
            print("  [+] Seguir buscando pulsado")
            await btn.click()
            await page.wait_for_timeout(2500)
        else: break

    # Buscar tarjetas de resultados
    locs = await page.locator("div:has-text('ACIERTOS')").all()
    for b in locs:
        try:
            txt = await b.inner_text()
            # Ignorar contenedores gigantes de toda la página
            if len(txt) > 1200:
                continue
            m = re.search(r"(\d+)/20", txt)
            if m:
                n = int(m.group(1))
                if n >= 14: # 70%+ histórico
                    lines = [l.strip() for l in txt.split("\n") if l.strip()]
                    partido = next((l.replace("PARTIDO","").strip() for l in lines if " vs " in l), "Partido del día")
                    mercado = next((l for l in lines if any(k in l.lower() for k in ["más de","menos de","tiros","corners","córners","faltas","tarjetas"])), "Línea L20")
                    p = n / 20.0
                    cards.append({
                        "comp": lines[0] if lines else "Fútbol",
                        "partido": partido,
                        "hora": "Hoy",
                        "nombre": lines[2] if len(lines) > 2 else tipo,
                        "equipo": lines[3] if len(lines) > 3 else "",
                        "mercado": mercado,
                        "casa": "WINAMAX",
                        "cuota": 1.85,
                        "l20": f"{n}/20",
                        "pct": f"{int(p*100)}%",
                        "pFinal": p,
                        "justa": round(1/p, 2),
                        "ev": round((1.85*p)-1, 2)
                    })
        except: continue
    return cards

async def run():
    todos = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(viewport={"width":1440,"height":900})).new_page()
        
        print("1. Iniciando sesión en ValueStats...")
        await page.goto("https://valuestats.com/login", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        # Rellenar solo casillas VISIBLES (ignora los tokens ocultos)
        await page.locator("input:visible").nth(0).fill(USER)
        await page.locator("input[type='password']:visible").first.fill(PASS)
        await page.locator("button[type='submit'], button:has-text('Iniciar sesión'), button:has-text('Entrar')").first.click()
        print("Credenciales enviadas con éxito.")
        await page.wait_for_timeout(5000)

        print("2. Entrando al Radar de Props...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        # 1. JUGADORES
        print("3. Buscando JUGADORES...")
        await click_txt(page, "Jugadores")
        await click_txt(page, "L20", exact=True)
        await click_txt(page, "Todas", exact=True)
        await click_txt(page, "Buscar candidatos")
        await page.wait_for_timeout(6000)
        
        jugs = await get_cards(page, "Jugador")
        print(f"-> Jugadores con 14/20 o más: {len(jugs)}")
        todos.extend(jugs)

        # 2. EQUIPOS
        print("4. Buscando EQUIPOS...")
        await click_txt(page, "Equipos")
        mercados = ["Córners del equipo", "Tiros del equipo", "Tiros a puerta del equipo", "Faltas del equipo", "Tarjetas del equipo"]
        for m in mercados:
            print(f"Mercado: {m}")
            try:
                sel = page.locator("div:has-text('Mercado')").locator("..").locator("div, select").first
                await sel.click()
                await click_txt(page, m)
            except: pass
            await click_txt(page, "Todas", exact=True)
            await click_txt(page, "L20", exact=True)
            await
