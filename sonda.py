from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
EVT = "https://betway.es/es/es/sports/evt/17389342"
TITULOS = ["Paradas del portero", "Tiros", "Fuera de juego", "Entradas",
           "Faltas", "Tarjetas", "Asiste 1+ Goles",
           "Tiros A Puerta Especiales"]
JS_TAB = (
    "p=>{const e=document.querySelector('li[data-testid=\"'+p+'\"]');"
    "if(!e)return false;e.click();return true}")
JS_CLICK = (
    "t=>{const l=Array.from(document.querySelectorAll('*')).filter("
    "e=>e.children.length===0&&e.innerText&&e.innerText.trim()===t);"
    "if(!l.length)return -1;l[l.length-1].click();return l.length}")
JS_ATTR = (
    "t=>{const l=Array.from(document.querySelectorAll('*')).filter("
    "e=>e.children.length===0&&e.innerText&&e.innerText.trim()===t);"
    "if(!l.length)return 'sin elemento';let e=l[l.length-1],s='';"
    "for(let i=0;i<4&&e;i++){s+=e.tagName+'['+(e.getAttribute("
    "'aria-expanded')||'')+'|'+(e.getAttribute('data-testid')||'')+'] ';"
    "e=e.parentElement}return s}")


def largo(pg):
    return len(pg.inner_text("body"))


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 3000})
    pg = ctx.new_page()
    pg.goto(EVT, timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_selector("li[role=tab]", timeout=30000)
    pg.wait_for_timeout(5000)
    try:
        pg.get_by_text("Aceptar Todo", exact=True).first.click(timeout=6000)
    except Exception:
        pass
    pg.evaluate(JS_TAB, "players")
    pg.wait_for_timeout(5000)
    for t in TITULOS:
        print("\n" + "=" * 50)
        print("SECCION:", t)
        print("atributos:", pg.evaluate(JS_ATTR, t))
        antes = largo(pg)
        r = pg.evaluate(JS_CLICK, t)
        pg.wait_for_timeout(2500)
        despues = largo(pg)
        print("click:", r, "| texto antes/despues:", antes, despues)
        if despues < antes:
            pg.evaluate(JS_CLICK, t)
            pg.wait_for_timeout(2500)
            print("estaba abierta: pulsada otra vez; ahora", largo(pg))
    pg.evaluate(
        "()=>document.querySelectorAll('*').forEach(e=>{if(e.children."
        "length===0&&e.innerText&&e.innerText.trim().startsWith("
        "'Ver todas'))e.click()})")
    pg.wait_for_timeout(3000)
    t = pg.inner_text("body")
    i = t.find("Paradas del portero")
    j = t.find("Reglas sobre apuestas")
    z = t[i:j if j > i else i + 9000].replace("\n", " | ")
    print("\n\n=== TEXTO COMPLETO jugadores (parte 1) ===")
    print(z[:6000])
    print("\n=== (parte 2) ===")
    print(z[6000:12000])
    br.close()
print("fin")
