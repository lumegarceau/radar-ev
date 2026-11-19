"""Sonda SIN proxy: ¿donde estan Brasileirao, Jupiler, 2. Bundesliga, Super Lig y Superliga en Sportium, Marca, Kirolbet(Juegging) y Betway?"""
import re
import time
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CLAVE = re.compile(r"brasil|brazil|brasileir|belg|jupiler|pro league|bundesliga ?2|2\.? ?bundesliga|segunda bundesliga|turqu|turkey|t[uü]rk|s[uü]per ?lig|dinamarca|denmark|superliga|danish", re.I)
JS_COMP = """()=>Array.from(document.querySelectorAll('a[href*="/competitions/"]'))
  .map(a=>({h:a.getAttribute('href'),t:(a.innerText||'').trim().slice(0,70)})).filter(x=>x.t)"""
JS_ANCH = """(p)=>Array.from(document.querySelectorAll('a')).map(a=>({h:a.getAttribute('href')||'',t:(a.innerText||'').trim().slice(0,70)})).filter(x=>x.h.indexOf(p)>=0&&x.t)"""
JS_IDS = "()=>Array.from(document.querySelectorAll('[data-eventid]')).map(e=>e.getAttribute('data-eventid'))"


def aceptar(pg):
    for t in ("Aceptar", "Aceptar todas las cookies", "Aceptar todo", "Permitir todas"):
        try:
            pg.get_by_text(t, exact=True).first.click(timeout=1500)
            return
        except Exception:
            pass


def ir(pg, url, espera=9000):
    try:
        pg.goto(url, timeout=60000, wait_until="domcontentloaded")
    except Exception as e:
        print("   goto falla", url[-60:], repr(e)[:70])
        return False
    pg.wait_for_timeout(espera)
    aceptar(pg)
    pg.wait_for_timeout(5000)
    return True


def sportium_marca(br):
    for nombre, base in (("SPORTIUM", "https://www.sportium.es"), ("MARCA", "https://www.marcaapuestas.es")):
        print("\n=====", nombre)
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 3000})
        pg = ctx.new_page()
        hall = {}
        for ruta in ("/apuestas/sports/soccer/competitions", "/apuestas/sports/soccer/matches", "/apuestas"):
            if not ir(pg, base + ruta):
                continue
            for x in pg.evaluate(JS_COMP):
                m = re.search(r"/competitions/(\d+)", x["h"])
                if m:
                    hall[m.group(1)] = x["t"].replace("\n", " ")
        print("competiciones descubiertas:", len(hall))
        for k, v in sorted(hall.items(), key=lambda z: z[1]):
            marca = "  <<<<<<" if CLAVE.search(v) else ""
            print("   ", k, v, marca)
        ctx.close()


def juegging(br):
    print("\n===== JUEGGING (Kirolbet)")
    base = "https://apuestas.juegging.es"
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 4000})
    pg = ctx.new_page()
    hall = {}
    for ruta in ("/esp/Sport", "/esp/Sport/Competicion/2881", "/esp/Sport/Competicion/3"):
        if not ir(pg, base + ruta, 10000):
            continue
        for x in pg.evaluate(JS_ANCH, "/Competicion/"):
            m = re.search(r"/Competicion/(\d+)", x["h"])
            if m:
                hall[m.group(1)] = x["t"].replace("\n", " ")
    print("competiciones descubiertas:", len(hall))
    for k, v in sorted(hall.items(), key=lambda z: int(z[0])):
        print("   ", k, v, "  <<<<<<" if CLAVE.search(v) else "")
    # otros enlaces del menu que mencionen las ligas
    ot = [x for x in pg.evaluate(JS_ANCH, "/esp/") if CLAVE.search(x["t"])]
    print("enlaces del menu que coinciden:", [(x["h"], x["t"]) for x in ot[:15]])
    ctx.close()


def betway(br):
    print("\n===== BETWAY")
    base = "https://betway.es/es/es/sports"
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 2400})
    pg = ctx.new_page()
    cand = ["brazil/serie-a", "brazil/brasileirao", "brazil/brasileirao-serie-a", "brazil/serie-a-betano",
            "belgium/jupiler-pro-league", "belgium/first-division-a", "belgium/pro-league",
            "germany/bundesliga-2", "germany/2-bundesliga", "germany/2nd-bundesliga",
            "turkey/super-lig", "turkey/super-lig-1", "turkey/trendyol-super-lig",
            "denmark/superliga", "denmark/superligaen", "denmark/super-liga"]
    for slug in cand:
        if not ir(pg, base + "/grp/soccer/" + slug, 6000):
            continue
        ids = pg.evaluate(JS_IDS)
        try:
            t = " ".join(pg.inner_text("body").split())[:90]
        except Exception:
            t = "?"
        print("  ", slug, "| url:", pg.url[-45:], "| partidos:", len(set(ids)), "|", t)
    # menu lateral
    ir(pg, base + "/grp/soccer/spain/la-liga", 6000)
    for x in pg.evaluate(JS_ANCH, "/grp/soccer/"):
        if CLAVE.search(x["t"]) or CLAVE.search(x["h"]):
            print("   MENU:", x["h"][-70:], "|", x["t"])
    ctx.close()


with sync_playwright() as p:
    br = p.chromium.launch()
    for f in (sportium_marca, juegging, betway):
        try:
            f(br)
        except Exception as e:
            print("FALLA", f.__name__, repr(e)[:150])
    br.close()
print("fin")
