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
                    api.append((r.url, r.request.method, r.status, r.text(), r.all_headers() if False else None, r.request.headers))
            except Exception:
                pass

        def fin(r):
            try:
                mb[0] += r.sizes().get("responseBodySize") or 0
            except Exception:
                pass
        pg.on("response", resp)
        pg.on("requestfinished", fin)
        pg.goto(BASE + "/sports/soccer-1001?tab=0", timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(5000)
        for tx in ("Permitir todas",):
            try:
                pg.get_by_text(tx, exact=True).first.click(timeout=4000)
            except Exception:
                pass
        pg.wait_for_timeout(18000)
        print("peticiones sportsapi:", len(api))
        for u, m, s, t, _, _h in api[:30]:
            print("  ", m, s, urllib.parse.unquote(u.split("sportsapi")[-1])[:150], "|", len(t))
        if not api:
            print("texto:", " ".join(pg.inner_text("body").split())[:400])
            return
        grande = max(api, key=lambda x: len(x[3]))
        d = json.loads(grande[3])
        print("\nRESPUESTA MAYOR:", grande[0][:170], "| bytes", len(grande[3]))
        resumen(d, "la respuesta")
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, dict) and v:
                    first = list(v.values())[0]
                    print("  ejemplo en '%s':" % k, json.dumps(first, ensure_ascii=False)[:700])
                elif isinstance(v, list) and v and isinstance(v[0], (dict, list)):
                    print("  ejemplo en '%s':" % k, json.dumps(v[0], ensure_ascii=False)[:700])
        print("\nNombres con tiro/falta/jugador/gol en las respuestas:", nombres([a[3] for a in api]))
        # cabeceras usadas
        h = {k: v for k, v in grande[5].items() if k.lower() not in ("cookie", "user-agent")}
        print("cabeceras de la peticion:", json.dumps(h)[:600])
        # llamada directa SIN navegador (misma cookie del contexto y con urllib puro)
        try:
            rq = ctx.request.get(grande[0], timeout=40000)
            print("\nDIRECTA con la sesion del navegador:", rq.status, len(rq.body()))
        except Exception as e:
            print("directa (sesion) falla:", repr(e)[:100])
        try:
            ph = urllib.request.ProxyHandler({"http": raw, "https": raw})
            op = urllib.request.build_opener(ph)
            rq2 = urllib.request.Request(grande[0], headers={"User-Agent": UA, "Accept": "application/json", "Origin": BASE, "Referer": BASE + "/"})
            body = op.open(rq2, timeout=40).read()
            print("DIRECTA con urllib puro y proxy:", 200, len(body))
        except Exception as e:
            print("DIRECTA con urllib puro falla:", repr(e)[:150])
        # entrar a un partido
        links = []
        for a in pg.locator("a[href*='/sports/']").all()[:400]:
            hh = a.get_attribute("href") or ""
            if hh not in links:
                links.append(hh)
        print("\nenlaces /sports/ distintos:", len(links))
        cand = [l for l in links if re.search(r"/(event|match|game|e)/|-\d{5,}", l)]
        print("candidatos a partido:", cand[:10])
        print("otros enlaces:", [l for l in links if l not in cand][:12])
        if cand:
            n0 = len(api)
            pg.goto(BASE + cand[0] if cand[0].startswith("/") else cand[0], timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(15000)
            print("\nPARTIDO:", pg.url[:130], "| peticiones nuevas:", len(api) - n0)
            for u, m, s, t, _, _h in api[n0:n0 + 20]:
                print("  ", m, s, urllib.parse.unquote(u.split("sportsapi")[-1])[:150], "|", len(t))
            print("nombres de mercados con tiro/falta/jugador:", nombres([a[3] for a in api[n0:]], 60))
            if len(api) > n0:
                gg = max(api[n0:], key=lambda x: len(x[3]))
                print("RESPUESTA MAYOR del partido:", gg[0][:170], "|", len(gg[3]))
                resumen(json.loads(gg[3]), "partido")
        print("\nMB aprox: %.2f" % (mb[0] / 1048576.0))
        ctx.close()
        br.close()


main()
