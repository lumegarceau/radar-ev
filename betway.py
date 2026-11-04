import asyncio
import json
import re
import time
from playwright.async_api import async_playwright
import rbway

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es/es/es/sports"
LIGAS = [
    "uefa-club-competitions/champions-league",
    "uefa-club-competitions/uefa-europa-league",
    "spain/la-liga",
    "spain/la-liga-2",
    "england/premier-league",
    "england/championship",
    "italy/serie-a",
    "france/ligue-1",
    "germany/bundesliga",
    "netherlands/eredivisie",
    "portugal/primeira-liga",
]
PEST = ["main-markets", "corners", "goals", "other"]
JS_TAB = (
    "p=>{const e=document.querySelector('li[data-testid=\"'+p+'\"]');"
    "if(!e)return false;e.click();return true}")
JS_MAS = (
    "()=>{let n=0;document.querySelectorAll('*').forEach(e=>{"
    "if(e.children.length===0&&e.innerText&&"
    "e.innerText.trim().startsWith('Ver todas')){e.click();n++}});"
    "return n}")
JS_IDS = (
    "()=>Array.from(document.querySelectorAll('[data-eventid]'))"
    ".map(e=>e.getAttribute('data-eventid'))")
LIMITE = 4


async def cookies(pg):
    try:
        await pg.get_by_text("Aceptar Todo", exact=True).first.click(
            timeout=5000)
    except Exception:
        pass


async def texto(pg):
    return rbway.lineas(await pg.inner_text("body"))


async def ids_liga(ctx, slug):
    pg = await ctx.new_page()
    try:
        await pg.goto(BASE + "/grp/soccer/" + slug, timeout=60000,
                      wait_until="domcontentloaded")
        await pg.wait_for_timeout(9000)
        await cookies(pg)
        ids = await pg.evaluate(JS_IDS)
        out = []
        for i in ids:
            if i not in out:
                out.append(i)
        print("liga", slug, "->", len(out), "partidos")
        return out
    except Exception as e:
        print("liga", slug, "fallo", repr(e)[:100])
        return []
    finally:
        await pg.close()


async def partido(ctx, eid, sem):
    async with sem:
        pg = await ctx.new_page()
        try:
            await pg.goto(BASE + "/evt/" + eid, timeout=60000,
                          wait_until="domcontentloaded")
            await pg.wait_for_selector("li[role=tab]", timeout=25000)
            await pg.wait_for_timeout(3000)
            l0 = await texto(pg)
            tit = [x for x in l0 if " vs. " in x]
            if not tit:
                return None
            c1, c2 = tit[0].split(" vs. ", 1)
            eq = []
            tot = []
            jug = {}
            ini = rbway.inicio(l0, c1)
            for p in PEST:
                if p != "main-markets":
                    if not await pg.evaluate(JS_TAB, p):
                        continue
                    await pg.wait_for_timeout(2500)
                e, t = rbway.parsear_mercados(await texto(pg), c1, c2)
                eq += e
                tot += t
            if await pg.evaluate(JS_TAB, "players"):
                for sub, stat in (("on-target", "sot"), ("shots", "shots")):
                    await pg.evaluate(JS_TAB, sub)
                    await pg.wait_for_timeout(2000)
                    await pg.evaluate(JS_MAS)
                    await pg.wait_for_timeout(2000)
                    for st, nom, n, c in rbway.parsear_jugadores(
                            await texto(pg), stat):
                        k = (st, nom, n)
                        if c > jug.get(k, 0):
                            jug[k] = c
            return {
                "id": eid, "c1": c1, "c2": c2, "inicio": ini,
                "equipo": eq, "total": tot,
                "jugador": [[a, b, c, d] for (a, b, c), d in jug.items()],
            }
        except Exception as e:
            print("partido", eid, "fallo", repr(e)[:100])
            return None
        finally:
            await pg.close()


async def main():
    t0 = time.time()
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        ctx = await br.new_context(
            user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
            viewport={"width": 1366, "height": 2400})
        ids = []
        for slug in LIGAS:
            for i in await ids_liga(ctx, slug):
                if i not in ids:
                    ids.append(i)
        print("partidos a leer:", len(ids))
        sem = asyncio.Semaphore(LIMITE)
        res = await asyncio.gather(*[partido(ctx, i, sem) for i in ids])
        res = [r for r in res if r]
        await br.close()
    ne = sum(len(r["equipo"]) for r in res)
    nt = sum(len(r["total"]) for r in res)
    nj = sum(len(r["jugador"]) for r in res)
    print("leidos:", len(res), "| equipo:", ne, "| totales:", nt,
          "| jugador:", nj, "|", round(time.time() - t0), "s")
    if res:
        json.dump({"ts": time.time(), "partidos": res},
                  open(rbway.ARCHIVO, "w"), ensure_ascii=False)
    else:
        print("sin datos: no se toca betway.json")


asyncio.run(main())
