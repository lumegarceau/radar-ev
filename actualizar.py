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
            print(f"  [OK] Clic en: {txt}")
            await page.wait_for_timeout(1000)
            return True
    except: pass
    print(f"  [--] No se vio: {txt}")
    return False

async def get_cards(page, tipo):
    cards = []
    for _ in range(5):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        btn = page.get_by_text("Seguir buscando").first
        if await btn.is_visible(timeout=1500):
            print("  [+] Clic en Seguir buscando")
            await btn.click()
            await page.wait_for_timeout(2500)
        else: break

    locs = await page.locator("div:has-text('ACIERTOS')").all()
    print(f"  -> Bloques con 'ACIERTOS' detectados: {len(locs)}")
    
    for b in locs:
        try:
            txt = await b.inner_text()
            m = re.search(r"(\d+)/20", txt)
            if m:
                n = int(m.group(1))
                if n >= 14:
                    lines = [l.strip() for l in txt.split("\n") if l.strip()]
                    partido = next((l.replace("PARTIDO","").strip() for l in lines if " vs " in l), "Partido")
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
        
        print("1. Entrando a ValueStats...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
        await click_txt(page, "Aceptar")

        # Login
        if await page.get_by_text("Iniciar sesión").first.is_visible(timeout=2500):
            print("Iniciando sesión...")
            await click_txt(page, "Iniciar sesión")
            await page.wait_for_timeout(1500)
            await page.locator("input[type='email'], input[name='email']").first.fill(USER)
            await page.locator("input[type='password'], input[name='password']").first.fill(PASS)
            await click_txt(page, "Iniciar sesión")
            await page.wait_for_timeout(4000)

        # 1. JUGADORES
        print("2. Buscando en JUGADORES...")
        await click_txt(page, "Jugadores")
        await click_txt(page, "L20", exact=True)
        await click_txt(page, "Todas", exact=True)
        await click_txt(page, "Buscar candidatos")
        await page.wait_for_timeout(6000)
        jugs = await get_cards(page, "Jugador")
        print(f"Jugadores extraídos: {len(jugs)}")
        todos.extend(jugs)

        # 2. EQUIPOS
        print("3. Buscando en EQUIPOS...")
        await click_txt(page, "Equipos")
        for m in ["Córners del equipo", "Tiros del equipo", "Tiros a puerta del equipo", "Faltas del equipo", "Tarjetas del equipo"]:
            print(f"Mercado: {m}")
            try:
                await page.locator("div:has-text('Mercado')").locator("..").locator("div, select").first.click()
                await click_txt(page, m)
            except: pass
            await click_txt(page, "Todas", exact=True)
            await click_txt(page, "L20", exact=True)
            await click_txt(page, "Buscar candidatos")
            await page.wait_for_timeout(5000)
            eqs = await get_cards(page, "Equipo")
            print(f"Equipos extraídos ({m}): {len(eqs)}")
            todos.extend(eqs)

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
    print(f"--- TOTAL FINAL GUARDADOS: {len(res)} ---")

if __name__ == "__main__":
    asyncio.run(run())
