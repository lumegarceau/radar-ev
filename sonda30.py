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
        import unicodedata

        def slug(t):
            t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower().replace(".", "")
            return re.sub(r"[^a-z0-9]+", "-", t).strip("-")
        evl = list(evs.values())[:4]
        liga_url = pg.url

        def hacer(e, modo):
            n0, m0 = len(api), mb[0]
            url = BASE + "/sports/event/%s-%s" % (slug(e["eventTitle"]), e["eventId"])
            try:
                if modo == "goto":
                    for intento in range(3):
                        try:
                            pg.goto(url, timeout=90000, wait_until="commit")
                            break
                        except Exception as ex2:
                            print("   reintento goto", intento + 1, repr(ex2)[:60])
                elif modo == "push":
                    pg.evaluate("(u)=>{history.pushState({},'',u);window.dispatchEvent(new PopStateEvent('popstate',{state:{}}))}", url.replace(BASE, ""))
                elif modo == "click":
                    pg.locator("a[href*='%s']" % e["eventId"]).first.click(timeout=8000)
            except Exception as ex:
                print("   falla", modo, repr(ex)[:90])
            pg.wait_for_timeout(16000)
            r = [x for x in api[n0:] if "eventview/normalized/%s" % e["eventId"] in x[0]]
            print("%s | %s | eventview: %d | %.2f MB" % (e["eventTitle"], modo, len(r), (mb[0] - m0) / 1048576.0))
            return json.loads(r[0][2]) if r else None
        det = hacer(evl[0], "goto")
        d2 = hacer(evl[1], "push")
        if not d2:
            d2 = hacer(evl[1], "goto")
        d3 = None
        try:
            pg.goto(liga_url, timeout=90000, wait_until="commit")
            pg.wait_for_timeout(6000)
            d3 = hacer(evl[2], "click")
        except Exception as ex:
            print("falla volver a liga", repr(ex)[:80])
        if det:
            md = det.get("marketsData") or {}
            print("\nCLAVES de un mercado:", sorted(next(iter(md.values())).keys()))
            vistos = {}
            for m in md.values():
                tn = m.get("marketTemplateName") or "?"
                if re.search(r"del Jugador|Jugador|Goleador|Anota", tn) and vistos.get(tn, 0) < 2:
                    vistos[tn] = vistos.get(tn, 0) + 1
                    outs = [(o.get("name"), o.get("title"), o.get("odds"), o.get("specifier"), o.get("competitorId"), o.get("playerId") or o.get("outcomeId")) for o in (m.get("outcomes") or [])[:6]]
                    print("\nMERCADO:", tn, "| name:", m.get("name"), "| specifiers:", m.get("specifiers"), "| n outcomes:", len(m.get("outcomes") or []))
                    print("   ", outs)
            m1 = next(m for m in md.values() if (m.get("marketTemplateName") or "") == "Faltas del Jugador")
            print("\nMERCADO COMPLETO (Faltas):", json.dumps(m1, ensure_ascii=False)[:1800])
        print("MB aprox: %.2f" % (mb[0] / 1048576.0))


if __name__ == "__main__":
    main()
