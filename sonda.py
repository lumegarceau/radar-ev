import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://apuestas.juegging.es"
EVENTO = BASE + "/esp/Sport/Evento/12067249"


def txt(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


def cargar(pg, url, minimo=3000):
    for _ in range(3):
        pg.goto(url, timeout=60000, wait_until="domcontentloaded")
        for _ in range(10):
            pg.wait_for_timeout(4000)
            if len(txt(pg)) > minimo:
                return True
    return False


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 4000})
    pg = ctx.new_page()
    print("== A. Competiciones")
    for cid in (6042, 1, 341, 3, 2, 321, 8622, 1019):
        try:
            ok = cargar(pg, "%s/esp/Sport/Competicion/%d" % (BASE, cid), 1500)
            ev = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href*=\"/Evento/\"]')).map(a=>a.getAttribute('href')+' '+(a.innerText||'').trim().replace(/\\s+/g,' ').slice(0,50))")
            print(cid, "|", pg.title(), "| cargada:", ok, "| eventos:", len(ev))
            for e in ev[:4]:
                print("      ", e)
        except Exception as e:
            print(cid, "falla", repr(e)[:80])
    print("\n== B. Pestaña FALTAS en bruto (con saltos de linea)")
    cargar(pg, EVENTO, 5000)
    pg.evaluate("""()=>{const e=Array.from(document.querySelectorAll('a')).find(x=>(x.innerText||'').trim().toUpperCase()==='FALTAS');if(e)e.click();}""")
    pg.wait_for_timeout(6000)
    t = pg.inner_text("body")
    i = t.upper().find("PARTICIPANTES")
    lineas = t[i:].split("\n")
    print("lineas totales desde PARTICIPANTES:", len(lineas))
    for k, l in enumerate(lineas[:130]):
        print(k, repr(l[:70]))
    print("\n== C. HTML del primer bloque")
    h = pg.evaluate("""()=>{const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
      while(n=w.nextNode()){ if(/participantes/i.test(n.nodeValue)){let p=n.parentElement;for(let i=0;i<2&&p.parentElement;i++)p=p.parentElement;return p.outerHTML.replace(/\\s+/g,' ').slice(0,3000);}}return 'no'}""")
    print(h)
    br.close()
