import re
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    return re.sub(r"\s+", " ", pg.inner_text("body"))


JS_EL = """()=>{
  const out=[];
  const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let n;
  while(n=w.nextNode()){
    if(/CHECA/i.test(n.nodeValue)&&/ESPA/i.test(n.nodeValue)){
      let e=n.parentElement;
      const r=e.getBoundingClientRect();
      let p=e,h=[];
      for(let i=0;i<5&&p;i++){h.push(p.tagName+'.'+(p.className||'')+' href='+(p.getAttribute('href')||'')+' onclick='+(p.getAttribute('onclick')||'').slice(0,120)+' id='+(p.id||''));p=p.parentElement;}
      out.push({txt:n.nodeValue.trim().slice(0,80),vis:[r.width,r.height],cadena:h});
    }
  }
  return out;}"""
JS_HREF = """()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href')).filter(h=>!/Account|Casino|Track|zendesk/i.test(h)).slice(0,60)"""

with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 3000})
    pg = ctx.new_page()
    pg.goto("https://apuestas.juegging.es/esp/Sport", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(12000)
    print("== A. Elementos con el partido")
    for x in pg.evaluate(JS_EL):
        print("  ", x)
    print("\n== B. Enlaces de la pagina")
    for h in pg.evaluate(JS_HREF):
        print("  ", h)
    print("\n== C. Pulsar por JS el partido")
    r = pg.evaluate("""()=>{
      const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
      while(n=w.nextNode()){ if(/CHECA/i.test(n.nodeValue)&&/ESPA/i.test(n.nodeValue)){n.parentElement.click();return 'ok';}}
      return 'no encontrado';}""")
    print("resultado:", r)
    pg.wait_for_timeout(12000)
    print("url:", pg.url)
    t = limpio(pg)
    print("longitud:", len(t))
    i = t.find("CHECA")
    print("texto:", t[max(i - 200, 0):max(i - 200, 0) + 2500])
    for w in ("Jugadores", "Tiros", "Córners", "Corners", "Faltas", "Tarjetas"):
        print("  ", w, "->", w.lower() in t.lower())
    br.close()
