import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
URL = "https://apuestas.juegging.es/esp/Sport/Evento/12067249"


def txt(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


JS_BLOQUE = """()=>{
  const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;const out=[];
  while(n=w.nextNode()){
    if(/^\\s*PARTICIPANTES\\s*$/.test(n.nodeValue)){
      let p=n.parentElement;
      for(let i=0;i<3&&p.parentElement;i++)p=p.parentElement;
      out.push(p.outerHTML.replace(/\\s+/g,' ').slice(0,2500));
      if(out.length>=2)break;
    }
  }
  return out;}"""
JS_TABS = """()=>Array.from(document.querySelectorAll('*')).filter(e=>e.children.length==0&&/^(TODOS|PRINCIPALES|GOLES|REMATES A PUERTA|JUGADORES|TARJETAS|FALTAS|PARADAS|PARTES|ESPECIALES)$/i.test((e.innerText||'').trim()))
  .map(e=>e.tagName+'.'+(e.className||'')+' | '+(e.innerText||'').trim()+' | parent='+e.parentElement.tagName+'.'+(e.parentElement.className||''))"""

with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 4000})
    pg = ctx.new_page()
    for intento in range(3):
        pg.goto(URL, timeout=60000, wait_until="domcontentloaded")
        for _ in range(12):
            pg.wait_for_timeout(5000)
            if len(txt(pg)) > 5000:
                break
        if len(txt(pg)) > 5000:
            break
    print("longitud:", len(txt(pg)))
    print("== A. Elementos de las pestañas")
    for x in pg.evaluate(JS_TABS):
        print("  ", x)
    print("\n== B. HTML de dos bloques de mercado (PARTICIPANTES)")
    for h in pg.evaluate(JS_BLOQUE):
        print(h)
        print("-----")
    for tab in ("REMATES A PUERTA", "JUGADORES", "FALTAS", "PARADAS", "TARJETAS"):
        print("\n== Pestaña", tab)
        try:
            pg.evaluate("""(t)=>{const e=Array.from(document.querySelectorAll('*')).find(x=>x.children.length==0&&(x.innerText||'').trim().toUpperCase()===t);if(e)e.click();}""", tab)
            pg.wait_for_timeout(6000)
            t = txt(pg)
            i = t.upper().find(tab, t.upper().find("TODOS"))
            print("longitud:", len(t))
            j = t.find("PARTES ESPECIALES")
            print(t[j:j + 1800] if j > 0 else t[:1800])
        except Exception as e:
            print("falla", repr(e)[:100])
    br.close()
