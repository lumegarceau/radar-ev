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
                    t
