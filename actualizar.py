import os, json, asyncio
from datetime import datetime
from playwright.async_api import async_playwright

USER = os.environ.get("VALUESTATS_USER")
PASS = os.environ.get("VALUESTATS_PASSWORD")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900}
        )
        page = await context.new_page()

        print("--- PASO 1: ENTRANDO A VALUESTATS ---")
        await page.goto("https://valuestats.com/login", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)

        titulo = await page.title()
        print(f"URL: {page.url}")
        print(f"TITULO: {titulo}")

        texto = await page.locator("body").inner_text()
        print("--- TEXTO EN PANTALLA ---")
        print(texto[:400].replace("\n", " | "))

        # Si hay campos de login, rellenamos
        inputs = await page.locator("input").count()
        print(f"Campos input detectados: {inputs}")

        if inputs >= 2:
            print("Rellenando usuario y contraseña...")
            await page.locator("input").nth(0).fill(USER)
            await page.locator("input").nth(1).fill(PASS)
            btn = page.locator("button[type='submit'], button:has-text('Iniciar'), button:has-text('Entrar')").first
            if await btn.is_visible():
                await btn.click()
                print("Pulsado botón de login.")
                await page.wait_for_timeout(5000)

        print("--- PASO 2: ENTRANDO A RADAR-PROPS ---")
        await page.goto("https://valuestats.com/radar-props", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)
        
        titulo_radar = await page.title()
        texto_radar = await page.locator("body").inner_text()
        print(f"RADAR URL: {page.url}")
        print(f"RADAR TITULO: {titulo_radar}")
        print("--- TEXTO RADAR ---")
        print(texto_radar[:400].replace("\n", " | "))

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
