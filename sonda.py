import re
from playwright.sync_api import sync_playwright
import rwina as rw

CLAVES = ["miami", "lafc", "los angeles", "seattle", "portland",
          "columbus", "cincinnati", "philadelphia", "atlanta united",
          "nashville", "vancouver", "toronto", "houston dynamo",
          "dallas", "colorado rapids", "salt lake", "san diego",
          "minnesota", "charlotte", "chicago fire", "orlando",
          "montreal", "red bulls", "new york city", "austin",
          "sporting kansas", "st. louis", "san jose", "d.c. united",
          "dc united", "new england", "galaxy"]
print("== Winamax: torneo de la MLS")
try:
    rw.conectar()
    d = rw.pedir("sport:1", "matches", 40)
    ms = d.get("matches", {})
    cuenta = {}
    for mid, m in ms.items():
        if not isinstance(m, dict):
            continue
        n = (str(m.get("competitor1Name", "")) + " v " +
             str(m.get("competitor2Name", "")))
        if any(c in n.lower() for c in CLAVES):
            t = m.get("srTournamentId")
            cuenta[t] = cuenta.get(t, 0) + 1
            print("  ", t, "|", n)
    print("torneos con equipos de MLS:", cuenta)
    print("partidos en torneo sr:tournament:242:",
          sum(1 for m in ms.values() if isinstance(m, dict)
              and m.get("srTournamentId") == "sr:tournament:242"))
    rw.cerrar()
except Exception as e:
    print("FALLO Winamax", repr(e)[:200])

print("\n== Betway: enlace y mercados de la MLS")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es/es/es/sports"
JS_IDS = ("()=>Array.from(document.querySelectorAll('[data-eventid]'))"
          ".map(e=>e.getAttribute('data-eventid'))")
JS_HREF = ("()=>Array.from(document.querySelectorAll('a[href]'))"
           ".map(a=>a.getAttribute('href'))")
JS_TAB = ("p=>{const e=document.querySelector('li[data-testid=\"'+p+'\"]');"
          "if(!e)return false;e.click();return true}")
PALABRAS = ["Córners", "Tarjetas", "Faltas", "Entradas", "Tiros",
            "Paradas del portero", "Fuera de juego"]
SLUGS = ["usa/mls", "united-states/mls", "usa/major-league-soccer",
         "united-states/major-league-soccer", "north-america/mls",
         "usa/mls-regular-season", "united-states-of-america/mls"]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2400})
    pg = ctx.new_page()
    try:
        pg.goto(BASE + "/grp/soccer", timeout=60000,
                wait_until="domcontentloaded")
        pg.wait_for_timeout(9000)
        try:
            pg.get_by_text("Aceptar Todo", exact=True).first.click(
                timeout=5000)
        except Exception:
            pass
        hs = pg.evaluate(JS_HREF)
        raros = sorted(set(h for h in hs if re.search(
            r"mls|usa|united-states|major-league", h or "", re.I)))
        print("enlaces con mls/usa en el menu:", raros[:20])
    except Exception as e:
        print("FALLO menu", repr(e)[:150])
        raros = []
    pg.close()
    probar = []
    for h in raros:
        m = re.search(r"/grp/soccer/(.+)$", h or "")
        if m and m.group(1) not in probar:
            probar.append(m.group(1))
    for s in SLUGS:
        if s not in probar:
            probar.append(s)
    ev = None
    for slug in probar[:12]:
        pg = ctx.new_page()
        try:
            pg.goto(BASE + "/grp/soccer/" + slug, timeout=60000,
                    wait_until="domcontentloaded")
            pg.wait_for_timeout(7000)
            ids = list(dict.fromkeys(pg.evaluate(JS_IDS)))
            print("slug", slug, "->", len(ids), "partidos")
            if ids and ev is None and re.search(
                    r"mls|major", slug, re.I):
                ev = (slug, ids[0])
        except Exception as e:
            print("slug", slug, "fallo", repr(e)[:80])
        pg.close()
    if ev:
        print("mercados del primer partido de", ev[0])
        pg = ctx.new_page()
        try:
            pg.goto(BASE + "/evt/" + ev[1], timeout=60000,
                    wait_until="domcontentloaded")
            pg.wait_for_selector("li[role=tab]", timeout=25000)
            pg.wait_for_timeout(3000)
            for tab in ["main-markets", "corners", "goals", "other",
                        "players"]:
                if tab != "main-markets":
                    if not pg.evaluate(JS_TAB, tab):
                        print("  pestana", tab, ": no existe")
                        continue
                    pg.wait_for_timeout(2500)
                t = pg.inner_text("body")
                print("  pestana", tab, ":",
                      [p for p in PALABRAS if p in t])
        except Exception as e:
            print("FALLO partido", repr(e)[:120])
        pg.close()
    else:
        print("no se encontro ningun partido de MLS en Betway")
    br.close()
print("fin")
# fin
