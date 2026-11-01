import os, json, asyncio, re
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def click_opt(page, sel):
    try:
        loc = page.locator(sel).first
        if await loc.is_visible(timeout=2500):
            await loc.click()
            await page.wait_for_timeout(800)
    except: pass

async def get_cards(page, tipo):
    cards = []
    for _ in range(5):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        btn = page.locator("button:has-text('Seguir buscando')").first
        if await btn.is_visible(timeout=1500):
            await btn.click()
            await page.wait_for_timeout(2000)
        else: break

    for b in await page.locator("div:has-text('ACIERTOS')").all():
        try:
            txt = await b.inner_text()
            m = re.search(r"(\d+)/20", txt)
            if m and int(m.group(1)) >= 14:
                n = int(m.group(1))
                lines = [l.strip() for l in txt.split("\n") if l.strip()]
                partido = next((l.replace("PARTIDO","").strip() for l in lines if " vs " in l), "Partido")
                mercado = next((l for l in lines if any(k in l.lower() for k in ["más de","menos de","tiros","corners","faltas","tarjetas"])), "Línea L20")
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
        
        print("1. Entrando...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        await click_opt(page, "button:has-text('Aceptar')")

        btn_log = page.locator("button:has-text('Iniciar sesión'), a:has-text('Iniciar sesión')").first
        if await btn_log.is_visible(timeout=2500):
            await btn_log.click()
            await page.wait_for_timeout(1500)
            await page.locator("input[type='email'], input[name='email']").first.fill(USER)
            await page.locator("input[type='password'], input[name='password']").first.fill(PASS)
            await click_opt(page, "button[type='submit'], button:has-text('Iniciar sesión')")
            await page.wait_for_timeout(4000)

        # 1. JUGADORES
        print("2. Jugadores...")
        await click_opt(page, "button:has-text('Jugadores')")
        await click_opt(page, "button:has-text('L20')")
        await click_opt(page, "button:has-text('Todas')")
        await click_opt(page, "button:has-text('Buscar candidatos')")
        await page.wait_for_timeout(5000)
        todos.extend(await get_cards(page, "Jugador"))

        # 2. EQUIPOS
        print("3. Equipos...")
        await click_opt(page, "button:has-text('Equipos')")
        for m in ["Córners del equipo", "Tiros del equipo", "Tiros a puerta del equipo", "Faltas del equipo", "Tarjetas del equipo"]:
            try:
                sel = page.locator("div:has-text('Mercado')").locator("..").locator("div, select").first
                await sel.click()
                await click_opt(page, f"li:has-text('{m}'), div:has-text('{m}')")
            except: pass
            await click_opt(page, "button:has-text('Todas')")
            await click_opt(page, "button:has-text('L20')")
            await click_opt(page, "button:has-text('Buscar candidatos')")
            await page.wait_for_timeout(4000)
            todos.extend(await get_cards(page, "Equipo"))

        await browser.close()

    # Guardar sin duplicados
    res = []
    vistos = set()
    for c in todos:
        k = f"{c['nombre']}_{c['mercado']}_{c['partido']}"
        if k not in vistos:
            vistos.add(k)
            res.append(c)

    ahora = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open("radar-data.json", "w", encoding="utf-8") as f:
        json.dump({"updated_at": ahora, "days": [{"candidatos": res}]}, f, indent=2, ensure_ascii=False)
    print(f"Total guardados: {len(res)}")

if __name__ == "__main__":
    asyncio.run(run())
