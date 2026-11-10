import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
BASE = "https://apuestas.juegging.es"

JS_COMP = """()=>Array.from(document.querySelectorAll('a[href*="/Competicion/"]')).map(a=>{
  const t=((a.innerText||a.textContent||'')+'').trim().replace(/\\s+/g,' ');
  return a.getAttribute('href')+' | '+t.slice(0,60)+' | title='+(a.getAttribute('title')||'')+' | des='+(a.getAttribute('des')||'')})"""
JS_CLICK = """(t)=>{const e=Array.from(document.querySelectorAll('a,li,span,div')).find(x=>x.children.length<=1&&(x.innerText||'').trim().toUpperCase()===t);
  if(e){e.click();return true}return false}"""


def cargar(pg, url):
    for _ in range(3):
        try:
            pg.goto(url, timeout=60000, wait_until="domcontentloaded")
        except Exception:
            continue
        for _ in range(8):
            pg.wait_for_timeout(3500)
            if len(pg.inner_text("body")) > 1500:
                return True
    return False


with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 4000})
    pg = ctx.new_page()
    cargar(pg, BASE + "/esp/Sport")
    vistos = set()

    def volcar(titulo):
        print("\n==", titulo)
        try:
            for x in pg.evaluate(JS_COMP):
                if x not in vistos:
                    vistos.add(x)
                    print("  ", x)
        except Exception as e:
            print("   falla", repr(e)[:80])

    volcar("Portada")
    for t in ("FÚTBOL", "ESPAÑA", "INGLATERRA", "ITALIA", "ALEMANIA", "FRANCIA", "EUROPA"):
        try:
            ok = pg.evaluate(JS_CLICK, t)
            pg.wait_for_timeout(5000)
            volcar("Tras pulsar %s (pulsado=%s)" % (t, ok))
        except Exception as e:
            print(t, "falla", repr(e)[:80])
    print("\n== Texto del menu lateral (primeros 1500 caracteres)")
    print(re.sub(r"\s+", " ", pg.inner_text("body"))[:1500])
    br.close()
