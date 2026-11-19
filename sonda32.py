"""Sonda CON proxy: ¿que ligas salen en la portada de futbol de Betsson y Betfair y como se llega a las 5 nuevas?"""
import json
import os
import re
import urllib.parse
from collections import Counter
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")
CLAVE = re.compile(r"brasil|brazil|brasileir|belg|jupiler|pro league|bundesliga ?2|2\.? ?bundesliga|segunda bundesliga|turqu|turkey|t[uü]rk|s[uü]per ?lig|dinamarca|denmark|superliga|danish", re.I)
JS_ANCH = """()=>Array.from(document.querySelectorAll('a')).map(a=>({h:a.getAttribute('href')||'',t:(a.innerText||'').trim().slice(0,70)})).filter(x=>x.h)"""


def proxy():
    raw = "".join(os.environ.get("PROXY_URL", "").split())
    if "://" not in raw:
        raw = "http://" + raw
    p = urllib.parse.urlparse(raw)
    return {"server": "%s://%s:%s" % (p.scheme, p.hostname, p.port),
            "username": urllib.parse.unquote(p.username or ""), "password": urllib.parse.unquote(p.password or "")}


def nuevo(br):
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 2500})
    ctx.add_init_script(STEALTH)
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())
    return ctx, pg


def betsson(br):
    print("\n===== BETSSON")
    ctx, pg = nuevo(br)
    bag = []

    def resp(r):
        try:
            if "/api/sb/v1/widgets/" in r.url and "json" in (r.headers.get("content-type") or ""):
                bag.append(r.text())
        except Exception:
            pass
    pg.on("response", resp)
    pg.goto("https://www.betsson.es/apuestas-deportivas/futbol", timeout=60000, wait_until="domcontentloaded")
    try:
        pg.get_by_text("Aceptar todas las cookies", exact=False).first.click(timeout=3000)
    except Exception:
        pass
    pg.wait_for_timeout(15000)
    evs = {}

    def busca(x, prof=0):
        if prof > 14:
            return
        if isinstance(x, dict):
            if x.get("startDate") and x.get("slug") and x.get("participants"):
                evs[x.get("slug")] = x
            for v in x.values():
                busca(v, prof + 1)
        elif isinstance(x, list):
            for v in x:
                busca(v, prof + 1)
    for t in bag:
        try:
            busca(json.loads(t))
        except Exception:
            pass
    print("eventos en la portada:", len(evs))
    if evs:
        e0 = next(iter(evs.values()))
        print("claves de un evento:", sorted(e0.keys()))
        print("ejemplo (recortado):", json.dumps({k: e0[k] for k in e0 if k in ("slug", "name", "competition", "league", "tournament", "category", "region", "path", "startDate", "phase")}, ensure_ascii=False)[:500])
        print("slugs de ejemplo:", [e["slug"][:90] for e in list(evs.values())[:6]])
        pref = Counter("/".join(e["slug"].split("/")[:3])[:60] for e in evs.values())
        print("prefijos de slug:", pref.most_common(30))
    an = pg.evaluate(JS_ANCH)
    print("enlaces totales:", len(an))
    for x in an:
        if CLAVE.search(x["t"]) or CLAVE.search(urllib.parse.unquote(x["h"])):
            print("   ENLACE:", x["h"][:110], "|", x["t"])
    print("enlaces /futbol/ (muestra):", [x["h"][:70] for x in an if "/futbol/" in x["h"]][:25])
    ctx.close()


def betfair(br):
    print("\n===== BETFAIR")
    ctx, pg = nuevo(br)
    bag = []
    pg.on("response", lambda r: bag.append(r.text()) if ("bff-gql" in r.url and "json" in (r.headers.get("content-type") or "")) else None)
    pg.goto("https://www.betfair.es/apuestas/f%C3%BAtbol/s-1", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    urls = []
    for t in bag:
        for u in re.findall(r'f%C3%BAtbol/[^"\\?]+/e-\d+', t):
            if u not in urls:
                urls.append(u)
    print("partidos en la portada:", len(urls))
    ligas = Counter("/".join(urllib.parse.unquote(u).split("/")[1:-2]) for u in urls)
    print("ligas en la portada:", ligas.most_common(40))
    print("ejemplo:", [urllib.parse.unquote(u) for u in urls[:4]])
    an = pg.evaluate(JS_ANCH)
    print("enlaces totales:", len(an))
    for x in an:
        if CLAVE.search(x["t"]) or CLAVE.search(urllib.parse.unquote(x["h"])):
            print("   ENLACE:", x["h"][:120], "|", x["t"])
    # textos de las respuestas que mencionen las ligas
    for t in bag:
        for m in re.finditer(r'"([^"]{3,80})"', t):
            s = m.group(1)
            if CLAVE.search(s) and len(s) < 70 and "e-" not in s[:3]:
                print("   TEXTO:", s)
                break
    ctx.close()


with sync_playwright() as p:
    br = p.chromium.launch(proxy=proxy())
    for f in (betsson, betfair):
        try:
            f(br)
        except Exception as e:
            print("FALLA", f.__name__, repr(e)[:150])
    br.close()
print("fin")
