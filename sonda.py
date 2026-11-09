import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
RUIDO = ("fullstory", "cookiebot", "google", "doubleclick", "ptplatforms", "framegas",
         "facebook", "analytics", "gstatic", "hotjar", "clarity")


def prueba(nom, url):
    print("\n=====", nom, url)
    reqs, wss, bodies = [], [], []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 2600})
        pg = ctx.new_page()

        def on_req(r):
            u = r.url
            if r.resource_type in ("image", "font", "stylesheet", "media"):
                return
            if any(x in u for x in RUIDO):
                return
            reqs.append((r.method, r.resource_type, u[:170]))

        def on_resp(r):
            try:
                u = r.url
                if any(x in u for x in RUIDO) or r.resource_type in ("image", "font", "stylesheet", "media"):
                    return
                b = r.body()
                t = b[:800000].decode("utf-8", "ignore")
                if len(t) > 800 and re.search(r"Italia|Francia|Chequia|Croacia|Inglaterra", t):
                    bodies.append((r.status, len(b), r.headers.get("content-type", "")[:40], u[:170], t))
            except Exception:
                pass

        def on_ws(ws):
            info = {"url": ws.url[:170], "recv": [], "sent": []}
            wss.append(info)
            ws.on("framereceived", lambda p: info["recv"].append(str(p)[:400]) if len(info["recv"]) < 14 else None)
            ws.on("framesent", lambda p: info["sent"].append(str(p)[:300]) if len(info["sent"]) < 6 else None)

        pg.on("request", on_req)
        pg.on("response", on_resp)
        pg.on("websocket", on_ws)
        try:
            r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("estado", r.status if r else None)
            pg.wait_for_timeout(6000)
            for t in ["Aceptar"]:
                try:
                    pg.get_by_text(t, exact=True).first.click(timeout=2500)
                except Exception:
                    pass
            pg.wait_for_timeout(18000)
            for _ in range(3):
                pg.mouse.wheel(0, 1500)
                pg.wait_for_timeout(1500)
            t = re.sub(r"\s+", " ", pg.inner_text("body"))
            i = t.find("Nations")
            print("URL final:", pg.url, "| texto", len(t))
            print("texto desde 'Nations':", t[max(0, i - 50):i + 1800])
            hs = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))")
            print("enlaces de partidos:", sorted(set(h for h in hs if re.search(r"/matches/|/events/|/event/", h or "")))[:8])
        except Exception as e:
            print("FALLO", repr(e)[:200])
        br.close()
    print("\npeticiones (sin ruido):", len(reqs))
    vistos = set()
    for m, t, u in reqs:
        k = (t, u.split("?")[0])
        if k in vistos:
            continue
        vistos.add(k)
        if t in ("xhr", "fetch", "websocket", "other", "eventsource") or "sportswidget" in u or "api" in u.lower():
            print("  ", m, t, u)
    print("\nwebsockets:", len(wss))
    for w in wss:
        print("  WS", w["url"])
        for s in w["sent"]:
            print("     >>", s[:300])
        for s in w["recv"][:8]:
            print("     <<", s[:400])
    print("\ncuerpos con nombres de selecciones:", len(bodies))
    for st, n, ct, u, t in bodies[:6]:
        i = re.search(r"Italia|Francia|Chequia|Croacia|Inglaterra", t).start()
        print("  ", st, n, ct, u)
        print("     ", t[max(0, i - 300):i + 700].replace("\n", " "))


prueba("Sportium", "https://www.sportium.es/apuestas/sports/soccer/competitions/46767/matches")
prueba("Marca Apuestas", "https://www.marcaapuestas.es/apuestas/sports/soccer/competitions/556801/matches")
print("\nfin")
