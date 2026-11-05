from playwright.sync_api import sync_playwright
import rbway

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://betway.es/es/es/sports"
JS_TAB = (
    "p=>{const e=document.querySelector('li[data-testid=\"'+p+'\"]');"
    "if(!e)return false;e.click();return true}")
JS_MAS = (
    "()=>{let n=0;document.querySelectorAll('*').forEach(e=>{"
    "if(e.children.length===0&&e.innerText&&"
    "e.innerText.trim().startsWith('Ver todas')){e.click();n++}});"
    "return n}")
JS_IDS = (
    "()=>Array.from(document.querySelectorAll('[data-eventid]'))"
    ".map(e=>e.getAttribute('data-eventid'))")
JS_TIT = (
    "t=>{const l=Array.from(document.querySelectorAll('*')).filter("
    "e=>e.children.length===0&&e.innerText&&e.innerText.trim()===t);"
    "if(!l.length)return false;l[l.length-1].click();return true}")
SECCIONES = ["Fuera de juego", "Entradas", "Faltas", "Tarjetas",
             "Paradas del portero"]


def mostrar(pg, etiqueta):
    t = pg.inner_text("body")
    lns = rbway.lineas(t)
    idx = [i for i, x in enumerate(lns) if "Paradas" in x]
    print("---", etiqueta, "| car:", len(t), "| lineas con Paradas:",
          [(i, lns[i]) for i in idx][:6])
    if idx:
        i = idx[0]
        print("   siguientes:", " | ".join(lns[i:i + 22]))
    sv = [x for x in rbway.parsear_jugadores(lns, "sot")
          if x[0] == "saves_eq"]
    print("   saves_eq parseado:", sv[:6])


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2400})
    pg = ctx.new_page()
    pg.goto(BASE + "/grp/soccer/uefa-club-competitions/uefa-europa-league",
            timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(9000)
    try:
        pg.get_by_text("Aceptar Todo", exact=True).first.click(timeout=8000)
    except Exception:
        pass
    ids = []
    for i in pg.evaluate(JS_IDS):
        if i not in ids:
            ids.append(i)
    print("eventos:", len(ids))
    for eid in ids[:2]:
        print("\n" + "=" * 50)
        print("EVENTO", eid)
        p2 = ctx.new_page()
        p2.goto(BASE + "/evt/" + eid, timeout=60000,
                wait_until="domcontentloaded")
        p2.wait_for_selector("li[role=tab]", timeout=25000)
        p2.wait_for_timeout(3000)
        print("titulo:", [x for x in rbway.lineas(p2.inner_text("body"))
                          if " vs. " in x][:1])
        print("players:", p2.evaluate(JS_TAB, "players"))
        p2.wait_for_timeout(4000)
        mostrar(p2, "tras abrir players")
        for sec in SECCIONES:
            antes = len(p2.inner_text("body"))
            ok = p2.evaluate(JS_TIT, sec)
            p2.wait_for_timeout(1500)
            desp = len(p2.inner_text("body"))
            print("seccion", sec, "| clic:", ok, "| antes/despues:",
                  antes, desp)
            if ok and desp < antes:
                p2.evaluate(JS_TIT, sec)
                p2.wait_for_timeout(1500)
                print("   reabierta, car:", len(p2.inner_text("body")))
            if sec == "Paradas del portero":
                mostrar(p2, "tras tocar Paradas")
        for sub in ("on-target", "shots"):
            print("subpestana", sub, p2.evaluate(JS_TAB, sub))
            p2.wait_for_timeout(2500)
            p2.evaluate(JS_MAS)
            p2.wait_for_timeout(2500)
            mostrar(p2, "tras " + sub)
        p2.close()
    br.close()
print("fin")
