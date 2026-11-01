import os, json, asyncio, re
from datetime import datetime
from playwright.async_api import async_playwright

U, P = os.environ.get("VALUESTATS_USER"), os.environ.get("VALUESTATS_PASSWORD")

async def run():
    cands = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await (await browser.new_context(viewport={"width":1440,"height":900})).new_page()
        
        print("1. Login en ValueStats...")
        await page.goto("https://valuestats.com/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        await page.locator("input:visible").nth(0).fill(U)
        await page.locator("input[type='password']:visible").first.fill(P)
        await page.locator("button[type='submit'], button:has-text('Iniciar')").first.click()
        await page.wait_for_timeout(5000)

        print("2. Radar de props...")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        async def scrape(tipo):
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                btn = page.get_by_text("Seguir buscando").first
                if await btn.is_visible(timeout=1500):
                    await btn.click()
                    await page.wait_for_timeout(2000)
                else: break

            for b in await page.locator("div:has-text('ACIERTOS')").all():
                try:
                    txt = await b.inner_text()
                    if len(txt) > 1200: continue
                    m = re.search(r"(\d+)/20", txt)
                    if m and int(m.group(1)) >= 14:
                        n = int(m.group(1))
                        lines = [l.strip() for l in txt.split("\n") if l.strip()]
                        cands.append({
                            "comp": lines[0] if lines else "Fútbol",
                            "partido": next((l.replace("PARTIDO","").strip() for l in lines if " vs " in l), "Partido"),
                            "hora": "Hoy",
                            "nombre": lines[2] if len(lines) > 2 else tipo,
                            "equipo": lines[3] if len(lines) > 3 else "",
                            "mercado": next((l for l in lines if any(k in l.lower() for k in ["más de","menos de","tiros","corners","córners","faltas","tarjetas"])), "L20"),
                            "casa": "WINAMAX",
                            "cuota": 1.85,
                            "l20": f"{n}/20",
                            "pct": f"{int((n/20)*100)}%",
                            "pFinal": n/20.0,
                            "justa": round(20.0/n, 2),
                            "ev": round(((1.85*(n/20.0))-1), 2)
                        })
                except: pass

        # Jugadores
        print("3. Buscando Jugadores...")
        for sel in ["Jugadores", "L20", "Todas", "Buscar candidatos"]:
            try: await page.get_by_text(sel, exact=(sel in ["L20","Todas"])).first.click()
            except: pass
            await page.wait_for_timeout(1000)
        await page.wait_for_timeout(5000)
        await scrape("Jugador")

        # Equipos
        print("4. Buscando Equipos...")
        try: await page.get_by_text("Equipos").first.click()
        except: pass
        for m in ["Córners del equipo", "Tiros del equipo", "Tiros a puerta del equipo", "Faltas del equipo", "Tarjetas del equipo"]:
            try:
                await page.locator("div:has-text('Mercado')").locator("..").locator("div, select").first.click()
                await page.get_by_text(m).first.click()
                for sel in ["Todas", "L20", "Buscar candidatos"]:
                    await page.get_by_text(sel, exact=(sel in ["L20","Todas"])).first.click()
            except: pass
            await page.wait_for_timeout(4000)
            await scrape("Equipo")

        await browser.close()

    unicos = list({f"{c['nombre']}_{c['mercado']}_{c['partido']}": c for c in cands}.values())
    ahora = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    with open("radar-data.json", "w", encoding="utf-8") as f:
        json.dump({"updated_at": ahora, "days": [{"candidatos": unicos}]}, f, indent=2, ensure_ascii=False)
    print(f"=== TOTAL GUARDADOS: {len(unicos)} ===")

if __name__ == "__main__":
    asyncio.run(run())
