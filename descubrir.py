import re
from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
WEB = "https://www.winamax.es/apuestas-deportivas"
frames = []


def vigila(ws):
    print("  websocket abierto:", ws.url[:120])
    ws.on("framesent", lambda p: frames.append(("ENV", p)))
    ws.on("framereceived", lambda p: frames.append(("REC", p)))


def texto(p):
    if isinstance(p, str):
        return p
    return str(p)


def resumen(n):
    print("  frames:", len(frames))
    for tipo, p in frames[:n]:
        t = texto(p)
        print("  ", tipo, len(t), t[:380].replace("\n", " "))


def palabras(pal, n):
    c = 0
    for tipo, p in frames:
        t = texto(p)
        m = re.search(pal, t)
        if not m:
            continue
        a = max(0, m.start() - 200)
        print("  ", tipo, t[a:m.end() + 300].replace("\n", " "))
        c += 1
        if c >= n:
            break
    print("  coincidencias mostradas:", c)


with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(
        locale="es-ES",
        timezone_id="Europe/Madrid",
        user_agent=UA,
        viewport={"width": 1280, "height": 900},
    )
    page = ctx.new_page()
    page.on("websocket", vigila)
    print("A) PORTADA")
    page.goto(WEB, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(15000)
    print("  titulo:", page.title())
    resumen(14)
    ids = []
    pats = [r'"matchId":(\d+)', r'"matches":\{"(\d+)"']
    for tipo, p in frames:
        t = texto(p)
        for pat in pats:
            for x in re.findall(pat, t):
                if x not in ids:
                    ids.append(x)
    print("  partidos vistos:", len(ids), ids[:6])
    if ids:
        frames.clear()
        print("")
        print("B) PARTIDO", ids[0])
        url = WEB + "/match/" + ids[0]
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(15000)
        print("  titulo:", page.title())
        resumen(8)
        print("  --- buscando corners")
        palabras(r"(?i)c[oó]rner|esquina", 4)
    b.close()
