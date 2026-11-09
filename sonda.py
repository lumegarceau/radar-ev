import re, difflib
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def limpio(pg):
    t = re.sub(r"\s+", " ", pg.inner_text("body"))
    k = t.find("Volver al inicio")
    return t[:k] if k > 0 else t


def nuevo(antes, despues):
    a, b = antes.split(), despues.split()
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("insert", "replace"):
            out.append(" ".join(b[j1:j2]))
    return " | ".join(out)[:1800]


JS_DOM = """()=>{
  const els=Array.from(document.querySelectorAll('*')).filter(e=>e.children.length==0&&(e.textContent||'').trim()==='Mercado');
  return els.slice(0,3).map(e=>{let p=e;for(let i=0;i<3&&p.parentElement;i++)p=p.parentElement;return p.outerHTML.slice(0,3500)});
}"""
JS_SEL = """()=>Array.from(document.querySelectorAll('select,[role=combobox],[role=listbox],[aria-haspopup],[class*=dropdown],[class*=Dropdown],[class*=select]'))
  .slice(0,25).map(e=>e.tagName+'|'+(e.getAttribute('role')||'')+'|'+(e.className&&e.className.toString().slice(0,70))+'|'+(e.innerText||'').trim().slice(0,50).replace(/\\s+/g,' '))"""


def prueba(nom, url):
    print("\n=====", nom, url)
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 3000})
        pg = ctx.new_page()
        try:
            pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(6000)
            try:
                pg.get_by_text("Aceptar", exact=True).first.click(timeout=2500)
            except Exception:
                pass
            pg.wait_for_timeout(12000)
            pg.get_by_text("Francia", exact=True).first.click(timeout=6000)
            pg.wait_for_timeout(12000)
            pg.get_by_text(re.compile(r"^Jugadores\b"), exact=False).first.click(timeout=4000)
            pg.wait_for_timeout(5000)
            print("HTML cerca de 'Mercado':")
            for h in pg.evaluate(JS_DOM):
                print("   ", re.sub(r"\s+", " ", h))
            print("\nselectores candidatos:")
            for s in pg.evaluate(JS_SEL):
                print("   ", s)
            # probar clic en el elemento 'Mercado' y en jugadores
            antes = limpio(pg)
            for intento in ["Mercado", "Jugador"]:
                try:
                    pg.locator("xpath=//*[normalize-space(text())='" + intento + "']").first.click(timeout=3000)
                    pg.wait_for_timeout(3000)
                    d = limpio(pg)
                    print("\nclic en", intento, "-> aparece:", nuevo(antes, d) or "(nada)")
                    antes = d
                except Exception as e:
                    print("\nclic en", intento, "falla:", repr(e)[:70])
            # clic en un jugador
            try:
                pg.get_by_text("Kylian Mbappe", exact=False).first.click(timeout=3000)
                pg.wait_for_timeout(4000)
                d = limpio(pg)
                print("\nclic en Mbappe -> aparece:", nuevo(antes, d) or "(nada)")
            except Exception as e:
                print("\nMbappe falla:", repr(e)[:70])
        except Exception as e:
            print("FALLO", repr(e)[:200])
        br.close()


prueba("Sportium", "https://www.sportium.es/apuestas/sports/soccer/competitions/46767/matches")
prueba("Marca Apuestas", "https://www.marcaapuestas.es/apuestas/sports/soccer/competitions/556801/matches")
print("\nfin")
