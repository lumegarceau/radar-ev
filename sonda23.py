"""Sonda Eldorado: SIN proxy, desde el servidor de GitHub."""
import json
import re
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")
PESADO = ("image", "media", "font")
PROV = re.compile(r"ultraplay|altenar|betby|digitain|sbtech|kambi|sportradar|betconstruct|softswiss|bti|pragmatic|sbgate|oddin|bet-?genius|metabet|gan\.|sportbook|sportsbook|odds|feed", re.I)
PAL = re.compile(r"tiro|remate|falta|jugador|player|shots?|fouls?|corner|c[oó]rner", re.I)
SITIOS = ["https://eldoradocasino.es/sports", "https://eldoradocasino.es/"]


def main():
    try:
        ip = json.load(urllib.request.urlopen("https://ipinfo.io/json", timeout=15))
        print("IP del servidor (sin proxy):", ip.get("ip"), ip.get("country"), ip.get("city"), ip.get("org"))
    except Exception as e:
        print("no sé la IP:", repr(e)[:80])
    with sync_playwright() as p:
        br = p.chromium.launch()
        for url in SITIOS:
            print("\n=====", url)
            ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                                 viewport={"width": 1366, "height": 2500})
            ctx.add_init_script(STEALTH)
            pg = ctx.new_page()
            pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
            hosts, js, ws, frames, mb = {}, [], [], [], [0]

            def req(r):
                h = urllib.parse.urlparse(r.url).netloc
                hosts[h] = hosts.get(h, 0) + 1

            def resp(r):
                try:
                    if "json" in (r.headers.get("content-type") or "").lower():
                        js.append((r.url, r.request.method, r.text(), r.request.post_data or ""))
                except Exception:
                    pass

            def fin(r):
                try:
                    mb[0] += r.sizes().get("responseBodySize") or 0
                except Exception:
                    pass

            def websock(w):
                rec = {"url": w.url, "n": 0, "ej": ""}
                ws.append(rec)

                def rx(d):
                    rec["n"] += 1
                    if len(rec["ej"]) < 600:
                        rec["ej"] += (d if isinstance(d, str) else str(d)[:80])[:300] + " || "
                w.on("framereceived", lambda d: rx(d))
            pg.on("request", req)
            pg.on("response", resp)
            pg.on("requestfinished", fin)
            pg.on("websocket", websock)
            try:
                r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
                print("estado:", r.status if r else None, "| url final:", pg.url[:120])
                for _ in range(6):
                    pg.wait_for_timeout(4000)
                    t = pg.title().lower()
                    if "momento" not in t and "just a moment" not in t and "verific" not in t:
                        break
                for tx in ("Aceptar todas", "Aceptar todo", "Aceptar", "Accept all"):
                    try:
                        b = pg.get_by_text(tx, exact=False).first
                        if b.count():
                            b.click(timeout=3000)
                            print("cookies:", tx)
                            break
                    except Exception:
                        pass
                pg.wait_for_timeout(20000)
                print("título:", pg.title()[:80])
                print("iframes:", [f.url[:110] for f in pg.frames][:8])
                print("dominios pedidos:", dict(sorted(hosts.items(), key=lambda kv: -kv[1])[:16]))
                print("dominios que suenan a apuestas:", sorted(h for h in hosts if PROV.search(h))[:15])
                print("websockets:", [(w["url"][:90], w["n"]) for w in ws][:5])
                for w in ws[:3]:
                    if w["ej"]:
                        print("  ejemplo de mensajes:", w["ej"][:500])
                for u, m, t, pd in sorted(js, key=lambda x: -len(x[2]))[:6]:
                    hit = sorted(set(x.group(0).lower() for x in PAL.finditer(t)))
                    print(" -", m, u[:140], "| bytes", len(t), "|", hit[:6])
                    if pd:
                        print("     cuerpo:", pd[:160])
                txt = " ".join(pg.inner_text("body").split())
                print("texto de la página:", txt[:600])
                links = []
                for a in pg.locator("a[href]").all()[:500]:
                    h = a.get_attribute("href") or ""
                    if re.search(r"f[uú]tbol|football|sport", h, re.I) and h not in links:
                        links.append(h)
                print("enlaces de deportes:", links[:15])
                print("MB aprox: %.2f" % (mb[0] / 1048576.0))
            except Exception as e:
                print("falla:", repr(e)[:150])
            ctx.close()
        br.close()


main()
