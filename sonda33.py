"""Sonda 33: resuelve los identificadores dudosos. Sin proxy: Sportium, Juegging, Betway. Con proxy: Betsson y Betfair."""
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
JS_ANCH = """()=>Array.from(document.querySelectorAll('a')).map(a=>({h:a.getAttribute('href')||'',t:(a.innerText||'').trim().replace(/\\s+/g,' ').slice(0,60)})).filter(x=>x.h)"""
JS_FILAS = """()=>{
  const out=[];const vistos=new Set();
  document.querySelectorAll('a[href*="/events/"]').forEach(a=>{
    const h=a.getAttribute('href');if(vistos.has(h))return;
    let p=a;
    for(let i=0;i<6&&p;i++){
      const t=(p.innerText||'');
      if(/\\d{1,2} [a-zA-Z]{3}\\w*,? \\d{2}:\\d{2}/.test(t)&&t.length<400){vistos.add(h);out.push({h:h,t:t});return;}
      p=p.parentElement;
    }
  });
  return out;}"""


def proxy():
    raw = "".join(os.environ.get("PROXY_URL", "").split())
    if "://" not in raw:
        raw = "http://" + raw
    p = urllib.parse.urlparse(raw)
    return {"server": "%s://%s:%s" % (p.scheme, p.hostname, p.port),
            "username": urllib.parse.unquote(p.username or ""), "password": urllib.parse.unquote(p.password or "")}


def ctxpg(br, h=3000, stealth=False, ligero=False):
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": h})
    if stealth:
        ctx.add_init_script(STEALTH)
    pg = ctx.new_page()
    if ligero:
        pg.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())
    return ctx, pg


def ir(pg, url, w=8000):
    try:
        pg.goto(url, timeout=60000, wait_until="domcontentloaded")
    except Exception as e:
        print("   goto falla", url[-60:], repr(e)[:60])
        return False
    pg.wait_for_timeout(w)
    for t in ("Aceptar", "Aceptar todas las cookies", "Aceptar todo", "Permitir todas"):
        try:
            pg.get_by_text(t, exact=True).first.click(timeout=1200)
            break
        except Exception:
            pass
    pg.wait_for_timeout(4000)
    return True


def sportium(br):
    print("\n===== SPORTIUM: que partidos hay en cada identificador dudoso")
    ctx, pg = ctxpg(br)
    for cid in (42382, 44743, 39511, 44806, 44674, 45985, 39496, 42039, 44860, 54776, 44571):
        if not ir(pg, "https://www.sportium.es/apuestas/sports/soccer/competitions/%s/matches" % cid, 7000):
            continue
        fs = pg.evaluate(JS_FILAS)
        print("  ", cid, "| partidos:", len(fs), "|", [" ".join(f["t"].split())[:70] for f in fs[:3]])
    ctx.close()


def juegging(br):
    print("\n===== JUEGGING (Kirolbet)")
    ctx, pg = ctxpg(br, 4000)
    for ruta in ("/esp/Sport", "/esp/Sport/Competicion/2881"):
        if not ir(pg, "https://apuestas.juegging.es" + ruta, 10000):
            continue
        html = pg.content()
        ids = Counter(re.findall(r"Competicion/(\d+)", html))
        print("  ", ruta, "| ids de competicion en el HTML:", dict(ids))
        an = pg.evaluate(JS_ANCH)
        print("   enlaces:", len(an), "| muestra:", [(x["h"][:50], x["t"]) for x in an[:30]])
        nombres = [m for m in re.findall(r">([^<>]{3,50})<", html) if re.search(r"Brasil|B[eé]lgica|Bundesliga|Turqu|Dinamarca|Super", m, re.I)]
        print("   textos con las ligas:", nombres[:20])
    ctx.close()


def betway(br):
    print("\n===== BETWAY: arbol de rutas")
    base = "https://betway.es/es/es/sports"
    ctx, pg = ctxpg(br, 2400)
    for ruta in ("/grp/soccer", "/grp/soccer/brazil", "/grp/soccer/germany"):
        if not ir(pg, base + ruta, 7000):
            continue
        an = [x for x in pg.evaluate(JS_ANCH) if "/grp/soccer/" in x["h"]]
        print("  ", ruta, "| enlaces de futbol:", len(an), "|", sorted(set(x["h"].split("/grp/soccer/")[-1] for x in an))[:60])
    for slug in ("brazil/brasileirao-serie-a", "brazil/serie-a-brazil", "brazil/brazil-serie-a", "brazil/campeonato-brasileiro-serie-a",
                 "germany/bundesliga-2", "germany/2-bundesliga", "germany/bundesliga-ii", "germany/2-liga", "germany/2.-bundesliga"):
        if ir(pg, base + "/grp/soccer/" + slug, 5000):
            ids = pg.evaluate("()=>Array.from(document.querySelectorAll('[data-eventid]')).map(e=>e.getAttribute('data-eventid'))")
            print("   ", slug, "| partidos:", len(set(ids)))
    ctx.close()


def betsson(br):
    print("\n===== BETSSON: paginas de pais")
    ctx, pg = ctxpg(br, 2500, True, True)
    bag = []

    def resp(r):
        try:
            if "/api/sb/v1/widgets/" in r.url and "json" in (r.headers.get("content-type") or ""):
                bag.append(r.text())
        except Exception:
            pass
    pg.on("response", resp)
    for pais in ("brasil", "belgica", "alemania", "turquia", "dinamarca"):
        n0 = len(bag)
        ir(pg, "https://www.betsson.es/apuestas-deportivas/futbol/" + pais, 9000)
        evs = {}

        def busca(x, prof=0):
            if prof > 14:
                return
            if isinstance(x, dict):
                if x.get("startDate") and x.get("slug") and x.get("participants"):
                    evs[x["slug"]] = x
                for v in x.values():
                    busca(v, prof + 1)
            elif isinstance(x, list):
                for v in x:
                    busca(v, prof + 1)
        for t in bag[n0:]:
            try:
                busca(json.loads(t))
            except Exception:
                pass
        comps = Counter((e.get("competitionName"), "/".join(e["slug"].split("/")[:3])) for e in evs.values())
        print("  ", pais, "| url final:", pg.url[-60:], "| eventos:", len(evs), "| competiciones:", comps.most_common(8))
    ctx.close()


def betfair(br):
    print("\n===== BETFAIR: enlaces de la portada")
    ctx, pg = ctxpg(br, 2500, True, True)
    bag = []
    pg.on("response", lambda r: bag.append(r.text()) if ("bff-gql" in r.url and "json" in (r.headers.get("content-type") or "")) else None)
    ir(pg, "https://www.betfair.es/apuestas/f%C3%BAtbol/s-1", 15000)
    an = pg.evaluate(JS_ANCH)
    print("enlaces:", len(an))
    for x in an:
        print("   ", urllib.parse.unquote(x["h"])[:100], "|", x["t"])
    n0 = len(bag)
    try:
        pg.get_by_text("Serie A Brasil", exact=True).first.click(timeout=5000)
        pg.wait_for_timeout(12000)
        urls = []
        for t in bag[n0:]:
            for u in re.findall(r'f%C3%BAtbol/[^"\\?]+/e-\d+', t):
                if u not in urls:
                    urls.append(u)
        print("tras pulsar 'Serie A Brasil' -> url:", urllib.parse.unquote(pg.url), "| partidos:", len(urls), "|", [urllib.parse.unquote(u)[:80] for u in urls[:5]])
    except Exception as e:
        print("no se pudo pulsar Serie A Brasil", repr(e)[:80])
    ctx.close()


with sync_playwright() as p:
    br = p.chromium.launch()
    for f in (sportium, juegging, betway):
        try:
            f(br)
        except Exception as e:
            print("FALLA", f.__name__, repr(e)[:150])
    br.close()
    br = p.chromium.launch(proxy=proxy())
    for f in (betsson, betfair):
        try:
            f(br)
        except Exception as e:
            print("FALLA", f.__name__, repr(e)[:150])
    br.close()
print("fin")
