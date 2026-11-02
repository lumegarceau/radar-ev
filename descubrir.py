import re
from playwright.sync_api import sync_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
WEB = "https://www.winamax.es/apuestas-deportivas"
frames = []


def vigila(ws):
    ws.on("framesent", lambda p: frames.append(("ENV", str(p))))
    ws.on("framereceived", lambda p: frames.append(("REC", str(p))))


def env(n):
    k = 0
    for tipo, t in frames:
        if tipo == "ENV" and len(t) > 12:
            print("   ENV", t[:500].replace("\n", " "))
            k += 1
            if k >= n:
                break


def rec(pal, n):
    k = 0
    for tipo, t in frames:
        if tipo != "REC":
            continue
        m = re.search(pal, t)
        if not m:
            continue
        a = max(0, m.start() - 250)
        print("   REC", len(t), t[a:m.end() + 450].replace("\n", " "))
        k += 1
        if k >= n:
            break
    print("   coincidencias:", k)


def cuerpo(page, n):
    try:
        t = page.inner_text("body")
        print("   texto:", t[:n].replace("\n", " | "))
    except Exception as e:
        print("   sin texto", str(e)[:80])


def enlaces(page, pat, n):
    try:
        hs = page.eval_on_selector_all(
            "a", "els => els.map(e => e.href)")
    except Exception:
        hs = []
    hs = sorted(set(h for h in hs if re.search(pat, h)))
    print("   enlaces", pat, len(hs), hs[:n])
    return hs


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

    print("A) SECCION FUTBOL")
    page.goto(WEB + "/sports/1", wait_until="domcontentloaded",
              timeout=60000)
    page.wait_for_timeout(15000)
    print("   titulo:", page.title())
    cuerpo(page, 700)
    enlaces(page, "match", 8)
    print("   frames:", len(frames))
    env(12)
    rec(r'"title"', 2)

    print("")
    print("B) CLIC EN LALIGA")
    frames.clear()
    for nombre in ("LaLiga", "La Liga", "España"):
        try:
            page.get_by_text(nombre, exact=True).first.click(timeout=8000)
            print("   clic en", nombre)
            break
        except Exception as e:
            print("   no hay", nombre, str(e)[:60])
    page.wait_for_timeout(12000)
    print("   url:", page.url)
    cuerpo(page, 600)
    hs = enlaces(page, "match", 8)
    env(8)
    rec(r"(?i)real madrid|barcelona|sevilla|osasuna", 2)

    print("")
    print("C) UN PARTIDO")
    frames.clear()
    try:
        if hs:
            page.goto(hs[0], wait_until="domcontentloaded", timeout=60000)
        else:
            page.get_by_text("Osasuna").first.click(timeout=8000)
        page.wait_for_timeout(15000)
        print("   url:", page.url)
        cuerpo(page, 900)
        env(8)
        print("   --- corners")
        rec(r"(?i)c[oó]rner|esquina", 3)
    except Exception as e:
        print("   fallo", str(e)[:120])
    b.close()
