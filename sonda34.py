"""Sonda 34 (proxy): ¿como se llega a la pagina de una liga en Betfair? Se mira dentro de un partido conocido."""
import json
import os
import re
import urllib.parse
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")
BASE = "https://www.betfair.es/apuestas/"


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
    bag = []
    pg.on("response", lambda r: bag.append((r.url, r.text())) if ("bff-gql" in r.url and "json" in (r.headers.get("content-type") or "")) else None)
    return ctx, pg, bag


def urls_de(bag, desde=0):
    out = []
    for _, t in bag[desde:]:
        for u in re.findall(r'f%C3%BAtbol/[^"\\?]+/e-\d+', t):
            if u not in out:
                out.append(u)
    return out


with sync_playwright() as p:
    br = p.chromium.launch(proxy=proxy())
    ctx, pg, bag = nuevo(br)
    pg.goto(BASE + "f%C3%BAtbol/s-1", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(15000)
    ev = urls_de(bag)
    print("partidos en la portada:", len(ev), [urllib.parse.unquote(u) for u in ev])
    br_ev = [u for u in ev if "serie-a-brasil" in u] or ev[:1]
    ctx.close()
    if br_ev:
        u = br_ev[0]
        print("\nabro:", urllib.parse.unquote(u))
        ctx, pg, bag = nuevo(br)
        pg.goto(BASE + u, timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(15000)
        print("respuestas gql:", len(bag))
        todo = "\n".join(t for _, t in bag)
        # patrones de enlaces de competicion
        for pat in (r'f%C3%BAtbol/[^"\\?/]+/c-\d+', r'/c-\d+', r'"competitionId"\s*:\s*"?[\w-]+', r'"competition[A-Za-z]*"\s*:\s*"[^"]{2,60}"',
                    r'f%C3%BAtbol/[^"\\?/]+(?=["\\?])', r'"(?:path|url|link|href)"\s*:\s*"[^"]*f%C3%BAtbol[^"]*"'):
            m = sorted(set(re.findall(pat, todo)))
            print("patron", pat[:45], "->", len(m), m[:12])
        for m in list(re.finditer(r"Serie A Brasil", todo))[:3]:
            print("CONTEXTO:", todo[max(0, m.start() - 250):m.end() + 250].replace("\n", " "))
        # enlaces del DOM
        an = pg.evaluate("()=>Array.from(document.querySelectorAll('a')).map(a=>a.getAttribute('href')||'').filter(h=>h)")
        print("enlaces DOM:", [urllib.parse.unquote(x)[:90] for x in an[:25]])
        ctx.close()
    # intentos de adivinar paginas de liga solo con el nombre
    for slug in ("serie-a-brasil", "jupiler-pro-league", "primera-division-belgica", "2-bundesliga", "bundesliga-2", "super-lig", "superliga-turquia", "superliga-dinamarca", "superligaen"):
        ctx, pg, bag = nuevo(br)
        try:
            pg.goto(BASE + "f%C3%BAtbol/" + slug, timeout=45000, wait_until="domcontentloaded")
            pg.wait_for_timeout(9000)
            ev = urls_de(bag)
            print("prueba", slug, "| url final:", urllib.parse.unquote(pg.url)[-60:], "| partidos:", len(ev), [urllib.parse.unquote(u)[:70] for u in ev[:3]])
        except Exception as e:
            print("prueba", slug, "falla", repr(e)[:60])
        ctx.close()
    br.close()
print("fin")
