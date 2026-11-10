import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
URL = "https://apuestas.juegging.es/esp/Sport/Evento/12067249"

with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 4000})
    pg = ctx.new_page()
    t = ""
    for intento in range(1, 4):
        pg.goto(URL, timeout=60000, wait_until="domcontentloaded")
        for _ in range(12):
            pg.wait_for_timeout(5000)
            t = re.sub(r"\s+", " ", pg.inner_text("body"))
            if len(t) > 5000:
                break
        print("intento", intento, "longitud", len(t))
        if len(t) > 5000:
            break
        print("   texto corto:", t[:400])
        pg.reload()
    print("longitud:", len(t))
    print("== A. Titulos de mercado (mayusculas)")
    tit = []
    for m in re.finditer(r"((?:[A-ZÁÉÍÓÚÑ0-9ºª¿?\(\),\.\-/ ]{6,}))(?= [A-Z0-9a-záéíóú])", t):
        s = m.group(1).strip()
        if len(s) > 5 and s not in tit:
            tit.append(s)
    print(tit[:150])
    print("\n== B. Extractos")
    for w in ("Faltas", "Paradas", "Córners", "Tarjetas", "Player "):
        idx = [m.start() for m in re.finditer(re.escape(w), t)]
        print("\n--", w, "apariciones:", len(idx))
        for i in idx[:3]:
            print("   ...", t[max(i - 60, 0):i + 420])
    open("evento.txt", "w", encoding="utf-8").write(t)
    br.close()
