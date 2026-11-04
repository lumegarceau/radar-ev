import json
import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es"
LIGA = BASE + "/es/es/sports/grp/soccer/spain/la-liga"
CLAVES = re.compile(r"c[oó]rner|esquina|tarjeta|remate|tiros|faltas", re.I)
reqs = []
resps = []


def on_req(r):
    if "betway" in r.url and r.resource_type in ("xhr", "fetch"):
        reqs.append((r.method, r.url, (r.post_data or "")[:300]))


def on_resp(r):
    try:
        if "betway" not in r.url or r.request.resource_type not in (
                "xhr", "fetch"):
            return
        resps.append((r.url, r.status, r.text()))
    except Exception:
        pass


def espera(pg, ms):
    pg.wait_for_timeout(ms)


def resumen(titulo):
    print("\n---", titulo, "---")
    print("peticiones internas:", len(reqs))
    vistos = set()
    for m, u, d in reqs:
        k = (m, u.split("?")[0])
        if k in vistos:
            continue
        vistos.add(k)
        print(" ", m, u[:150])
        if d:
            print("     POST:", d)
    print("respuestas con mercados:")
    for u, s, t in resps:
        m = CLAVES.search(t)
        if m:
            a = max(0, m.start() - 300)
            print("  >>", s, len(t), u[:120])
            print("     ", t[a:a + 700].replace("\n", " "))
            break
    else:
        print("  (ninguna)")


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    pg.on("request", on_req)
    pg.on("response", on_resp)
    pg.goto(LIGA, timeout=60000, wait_until="domcontentloaded")
    espera(pg, 15000)
    print("LIGA:", pg.url, "|", pg.title()[:70])
    print("texto:", pg.inner_text("body")[300:1500].replace("\n", " | "))
    hs = pg.eval_on_selector_all(
        "a[href]", "e=>e.map(x=>x.getAttribute('href'))")
    ev = []
    for h in hs:
        if h and h not in ev and re.search(
                r"/evt/|/event|/match|/e/|/fixture", h):
            ev.append(h)
    print("enlaces tipo partido:", ev[:10])
    otros = [h for h in hs if h and "/sports/" in h and not re.search(
        r"/cat/|/grp/|/hub/|/ext/|/live|/find|/sports$", h)]
    print("otros enlaces de sports:", otros[:10])
    resumen("pagina de la liga")
    ids = []
    for u, s, t in resps:
        if "getGroup" in u:
            for m in re.finditer(r'"EventId":(\d+)', t):
                if m.group(1) not in ids:
                    ids.append(m.group(1))
    print("\nEventIds de getGroup:", ids[:10])
    destino = None
    if ev:
        destino = ev[0]
    elif otros:
        destino = otros[0]
    elif ids:
        destino = "/es/es/sports/evt/" + ids[0]
    if destino:
        reqs.clear()
        resps.clear()
        if destino.startswith("/"):
            destino = BASE + destino
        pg.goto(destino, timeout=60000, wait_until="domcontentloaded")
        espera(pg, 15000)
        print("\nPARTIDO:", pg.url, "|", pg.title()[:70])
        print("texto:", pg.inner_text("body")[:2000].replace("\n", " | "))
        resumen("pagina del partido")
    br.close()
print("fin")
