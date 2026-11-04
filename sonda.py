import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es"
CLAVES = re.compile(r"c[oó]rner|esquina|tarjeta|remate|tiros|faltas", re.I)
jsons = []
frames = []


def resp(r):
    try:
        if "json" not in r.headers.get("content-type", ""):
            return
        if "betway" not in r.url:
            return
        jsons.append((r.url, r.text()))
    except Exception:
        pass


def ws(w):
    print("WEBSOCKET", w.url[:150])

    def rec(d):
        frames.append(str(d)[:500])
    w.on("framereceived", rec)


def enlaces(pg):
    hs = pg.eval_on_selector_all(
        "a[href]", "e=>e.map(x=>x.getAttribute('href'))")
    out = []
    for h in hs:
        if h and h not in out:
            out.append(h)
    return out


def ir(pg, u, esp=10000):
    if u.startswith("/"):
        u = BASE + u
    pg.goto(u, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(esp)
    print("\n>>> URL:", pg.url, "|", pg.title()[:60])
    print("texto:", pg.inner_text("body")[:400].replace("\n", " | "))


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    pg.on("response", resp)
    pg.on("websocket", ws)
    ir(pg, BASE + "/es/sports", 12000)
    hs = enlaces(pg)
    print("\nTODOS los enlaces (primeros 60):")
    for h in hs[:60]:
        print(" ", h)
    fut = [h for h in hs if re.search(r"soccer|futbol|football", h, re.I)]
    print("\nENLACES de futbol:", fut[:15])
    print("\n--- getGroup (2 primeros, 1500 car.) ---")
    n = 0
    for u, t in jsons:
        if "getGroup" in u and n < 2:
            n += 1
            print(u)
            print(t[:1500])
    if fut:
        ir(pg, fut[0], 12000)
        hs2 = enlaces(pg)
        print("\nEnlaces en la pagina de futbol (primeros 60):")
        for h in hs2[:60]:
            print(" ", h)
        cand = [h for h in hs2
                if re.search(r"soccer|futbol|football", h, re.I)
                and h.count("/") >= 7]
        print("\nCandidatos a partido:", cand[:10])
        if cand:
            jsons.clear()
            frames.clear()
            ir(pg, cand[0], 14000)
            print("\n--- JSON recibidos ---")
            for u2, t in jsons:
                tag = "MERCADOS" if CLAVES.search(t) else "-"
                print(tag, len(t), u2[:150])
            for u2, t in jsons:
                m = CLAVES.search(t)
                if m:
                    a = max(0, m.start() - 500)
                    print("\nEJEMPLO de", u2[:100])
                    print(t[a:a + 1500])
                    break
            print("\n--- websocket (primeros 10) ---")
            for f in frames[:10]:
                print(f)
    br.close()
print("fin")
