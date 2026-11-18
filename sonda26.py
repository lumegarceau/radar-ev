"""Sonda Eldorado a fondo (con proxy español): estructura de la API y mercados de jugador."""
import json
import os
import re
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")
PESADO = ("image", "media", "font")
PAL = re.compile(r"tiro|remate|falta|jugador|player|shots?|fouls?|offside|fuera de juego|gol", re.I)
BASE = "https://eldoradocasino.es"


def proxy():
    raw = "".join(os.environ.get("PROXY_URL", "").split())
    if "://" not in raw:
        raw = "http://" + raw
    u = urllib.parse.urlparse(raw)
    return {"server": "%s://%s:%s" % (u.scheme, u.hostname, u.port),
            "username": urllib.parse.unquote(u.username or ""),
            "password": urllib.parse.unquote(u.password or ""), "_raw": raw}


def caminar(x, f, prof=0):
    if prof > 30:
        return
    if isinstance(x, dict):
        f(x)
        for v in x.values():
            caminar(v, f, prof + 1)
    elif isinstance(x, list):
        for v in x:
            caminar(v, f, prof + 1)


def resumen(d, et):
    print("  --- estructura de", et)
    if isinstance(d, dict):
        for k, v in list(d.items())[:25]:
            if isinstance(v, dict):
                print("    %s: dict de %d | ej. clave %s" % (k, len(v), list(v)[:2]))
            elif isinstance(v, list):
                print("    %s: lista de %d" % (k, len(v)))
            else:
                print("    %s: %s" % (k, str(v)[:60]))


def nombres(textos, n=40):
    vistos = []

    def f(d):
        for k in ("name", "title", "marketName", "label", "displayName"):
            v = d.get(k)
            if isinstance(v, str) and PAL.search(v) and v not in vistos and len(vistos) < n:
                vistos.append(v)
    for t in textos:
        try:
            caminar(json.loads(t), f)
        except Exception:
            pass
    return vistos


def main():
    pr = proxy()
    raw = pr.pop("_raw")
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=pr)
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 2500})
        ctx.add_init_script(STEALTH)
        pg = ctx.new_page()
        pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
        api, mb = [], [0]

        def resp(r):
            try:
                if "sportsapi" in r.url and "json" in (r.headers.get("content-type") or "").lower():
                    api.append((r.url, r.status, r.text(), dict(r.request.headers)))
            except Exception:
                pass

        def fin(r):
            try:
                mb[0] += r.sizes().get("responseBodySize") or 0
            except Exception:
                pass
        pg.on("response", resp)
        pg.on("requestfinished", fin)
        pg.goto(BASE + "/sports/soccer-1001/laliga-19000000008?tab=matches", timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(5000)
        try:
            pg.get_by_text("Permitir todas", exact=True).first.click(timeout=4000)
        except Exception:
            pass
        pg.wait_for_timeout(15000)
        liga = [a for a in api if "multi-leagueview" in a[0]]
        print("respuestas de liga:", len(liga))
        if not liga:
            print("texto:", " ".join(pg.inner_text("body").split())[:300])
            return
        d = json.loads(liga[0][2])
        evs = d.get("events") or {}
        print("eventos en la liga:", len(evs))
        k0 = list(evs)[0]
        e0 = evs[k0]
        print("CLAVES DE UN EVENTO:", sorted(e0.keys()) if isinstance(e0, dict) else type(e0))
        print("EVENTO EJEMPLO:", json.dumps(e0, ensure_ascii=False)[:1500])
        print("TORNEO EJEMPLO:", json.dumps((d.get("tournaments") or [None])[0], ensure_ascii=False)[:400])
        print("marketTitles:", json.dumps(d.get("marketTitles"), ensure_ascii=False)[:300])
        hdr = {k: v for k, v in liga[0][3].items() if k.lower().startswith("x-platform") or k.lower() in ("accept", "accept-language")}
        print("cabeceras a reutilizar:", sorted(hdr))
        # enlaces a partidos
        links = []
        for a in pg.locator("a[href]").all()[:600]:
            h = a.get_attribute("href") or ""
            if re.search(r"/5\d{9,}", h) and h not in links:
                links.append(h)
        print("enlaces con id de partido:", links[:6])
        n0 = len(api)
        entrado = False
        if links:
            pg.goto(BASE + links[0] if links[0].startswith("/") else links[0], timeout=60000, wait_until="domcontentloaded")
            entrado = True
        else:
            nom = None
            def f(x):
                nonlocal nom
                if nom is None and isinstance(x, dict):
                    for kk in ("homeTeamName", "home", "homeName"):
                        if isinstance(x.get(kk), str):
                            nom = x[kk]
            caminar(e0, f)
            print("pruebo a pulsar el equipo:", nom)
            if nom:
                try:
                    pg.get_by_text(nom, exact=True).first.click(timeout=8000)
                    entrado = True
                except Exception as e:
                    print("no pulsa:", repr(e)[:100])
        pg.wait_for_timeout(15000)
        print("\nURL actual:", pg.url[:140], "| peticiones nuevas:", len(api) - n0)
        for u, s_, t, h in api[n0:n0 + 25]:
            print("  ", s_, urllib.parse.unquote(u.split("sportsapi")[-1])[:160], "|", len(t))
        nuevos = api[n0:]
        if nuevos:
            nm = nombres([x[2] for x in nuevos], 80)
            print("\nnombres con tiro/falta/jugador/gol:", nm)
            gg = max(nuevos, key=lambda x: len(x[2]))
            print("RESPUESTA MAYOR:", gg[0][:200], "|", len(gg[2]))
            try:
                dd = json.loads(gg[2])
                resumen(dd, "detalle del partido")
                if isinstance(dd, dict):
                    for kk, vv in dd.items():
                        if isinstance(vv, list) and vv and isinstance(vv[0], dict):
                            print("  ejemplo en '%s':" % kk, json.dumps(vv[0], ensure_ascii=False)[:600])
                        elif isinstance(vv, dict) and vv:
                            print("  ejemplo en '%s':" % kk, json.dumps(list(vv.values())[0], ensure_ascii=False)[:600])
            except Exception as e:
                print("no es JSON limpio:", repr(e)[:80])
        # reutilizar cabeceras dentro de la pagina (sin recargar nada)
        otra = BASE.replace("eldoradocasino.es", "hres-api.egt-digital.com") + "/api/sportsapi/public/sport-events/v2/multi-leagueview/normalized/1001?tournamentIds=19000000054&isLive=false&marketCount=3&viewType=multi"
        r = pg.evaluate("""async ([u,h])=>{const r=await fetch(u,{headers:h,credentials:'include'});const t=await r.text();return {s:r.status,n:t.length,ini:t.slice(0,120)}}""", [otra, hdr])
        print("\nPETICION PROPIA dentro de la pagina (otra liga):", r)
        print("MB aprox: %.2f" % (mb[0] / 1048576.0))
        ctx.close()
        br.close()


main()
