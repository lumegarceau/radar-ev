import json
import re
import sys
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import rsport

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CASAS = [
    {"nombre": "Sportium", "base": "https://www.sportium.es",
     "archivo": "sportium.json", "comp": {"Nations League": 46767}},
    {"nombre": "Marcaapuestas", "base": "https://www.marcaapuestas.es",
     "archivo": "marca.json", "comp": {"Nations League": 556801}},
]
# nombres de competicion que se buscan en el menu de futbol de cada casa
BUSCAR = ["LaLiga", "La Liga", "Segunda División", "Premier League",
          "Championship", "Serie A", "Ligue 1", "Bundesliga", "Eredivisie",
          "Primeira Liga", "Champions League", "Europa League", "MLS"]
# IDs de competicion fijos (los nombres de ambas webs se repiten entre paises)
IDS_LIGAS = {
    "sportium": {"La Liga": 45211, "Segunda": 45215, "Premier": 40527,
                 "Championship": 40602, "Serie A": 44571, "Ligue 1": 46074,
                 "Bundesliga": 45915, "Eredivisie": 43094,
                 "Primeira": 44979, "Champions": 45225, "Europa League": 45223,
                 "MLS": 44663},
    "marcaapuestas": {"La Liga": 19160, "Segunda": 48352, "Premier": 19157,
                      "Serie A": 19159, "Ligue 1": 19327, "Bundesliga": 19158,
                      "Eredivisie": 19358, "Primeira": 19211,
                      "Champions": 19161, "Europa League": 19162, "MLS": 19302},
}
HORAS = 80
MAX_EVENTOS = 30
LIMITE_S = 17 * 60
T0 = time.time()

JS_FILAS = """()=>{
  const out=[];const vistos=new Set();
  document.querySelectorAll('a[href*="/events/"]').forEach(a=>{
    const h=a.getAttribute('href');if(vistos.has(h))return;
    let p=a;
    for(let i=0;i<6&&p;i++){
      const t=(p.innerText||'');
      if(/\\d{1,2} [a-zA-Z]{3}\\w*,? \\d{2}:\\d{2}/.test(t)&&t.length<400){vistos.add(h);out.push({h:h,t:t});return;}
      p=p.parentElement;
    }
  });
  return out;}"""
JS_COMP = """()=>Array.from(document.querySelectorAll('a[href*="/competitions/"]'))
  .map(a=>({h:a.getAttribute('href'),t:(a.innerText||'').trim().slice(0,60)})).filter(x=>x.t)"""


def limpio(pg):
    t = re.sub(r"\s+", " ", pg.inner_text("body"))
    k = t.find("Volver al inicio")
    return t[:k] if k > 0 else t


def aceptar(pg):
    try:
        pg.get_by_text("Aceptar", exact=True).first.click(timeout=2500)
    except Exception:
        pass


def pulsar(pg, patron, espera=3500, exacto=False):
    try:
        loc = pg.get_by_text(patron, exact=exacto).first
        loc.click(timeout=3500)
        pg.wait_for_timeout(espera)
        return True
    except Exception:
        return False


def mostrar_todo(pg):
    for _ in range(14):
        try:
            b = pg.get_by_text(re.compile(r"^\s*mostrar todo\s*$", re.I))
            if b.count() == 0:
                break
            b.first.click(timeout=2500)
            pg.wait_for_timeout(1200)
        except Exception:
            break


def descubrir(pg, base):
    """Busca en el menu de futbol los enlaces de las competiciones."""
    hall = {}
    for ruta in ("/apuestas/sports/soccer/competitions",
                 "/apuestas/sports/soccer/matches", "/apuestas"):
        try:
            pg.goto(base + ruta, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(9000)
            aceptar(pg)
            pg.wait_for_timeout(8000)
            for x in pg.evaluate(JS_COMP):
                m = re.search(r"/competitions/(\d+)", x["h"])
                if m:
                    hall[m.group(1)] = x["t"]
            if len(hall) > 5:
                break
        except Exception as e:
            print("   descubrir falla", ruta, repr(e)[:80])
    print("   competiciones descubiertas:", len(hall))
    for k, v in sorted(hall.items(), key=lambda z: z[1]):
        print("      ", k, v.replace("\n", " "))
    sel = {}
    fijos = IDS_LIGAS.get(base.split("//")[-1].split("/")[0].split(".")[-2], {})
    for nombre, k in fijos.items():
        sel["%s #%s" % (nombre, k)] = k
    return sel


def filas_competicion(pg, base, cid, ahora):
    pg.goto("%s/apuestas/sports/soccer/competitions/%s/matches" % (base, cid),
            timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(8000)
    aceptar(pg)
    pg.wait_for_timeout(9000)
    out = []
    for f in pg.evaluate(JS_FILAS):
        ini = rsport.inicio_de(f["t"])
        eq = rsport.equipos_de_fila(f["t"])
        if not ini or not eq:
            continue
        if ini < ahora - 3600 or ini > ahora + HORAS * 3600:
            continue
        out.append({"h": f["h"], "inicio": ini, "c1": eq[0], "c2": eq[1]})
    return out


def leer_evento(ctx, base, fila):
    pg = ctx.new_page()
    c1, c2 = fila["c1"], fila["c2"]
    equipo, total, jug = [], [], []
    try:
        pg.goto(base + fila["h"], timeout=60000, wait_until="domcontentloaded")
        pg.wait_for_timeout(9000)
        aceptar(pg)
        pg.wait_for_timeout(5000)
        e, t = rsport.parsear_equipo(limpio(pg), c1, c2)
        equipo += e
        total += t
        if pulsar(pg, re.compile(r"^C[oó]rners\b", re.I)):
            e, t = rsport.parsear_equipo(limpio(pg), c1, c2)
            equipo += e
            total += t
            # equipos plegados (Marca): intentar desplegarlos
            for nom in (c1, c2):
                pulsar(pg, re.compile(r"^" + re.escape(nom) + r" C[oó]rners 2 Opciones$", re.I), 2500)
            e, t = rsport.parsear_equipo(limpio(pg), c1, c2)
            equipo += e
            total += t
        if pulsar(pg, re.compile(r"^Jugadores\b"), 4000):
            pulsar(pg, "Mercado", 4000, True)
            mostrar_todo(pg)
            o, res = rsport.parsear_jugadores(limpio(pg), c1, c2)
            vac = [k for k, v in res.items() if v == "sin_datos"]
            for tit in vac:
                if pulsar(pg, tit, 2500, True):
                    mostrar_todo(pg)
            if vac:
                o, res = rsport.parsear_jugadores(limpio(pg), c1, c2)
            jug = o
            print("      jugadores:", res)
        else:
            print("      sin pestana Jugadores")
    except Exception as e:
        print("      fallo evento", repr(e)[:120])
    pg.close()
    return equipo, total, jug


def dedup(lista):
    vistos, out = set(), []
    for x in lista:
        k = tuple(x)
        if k not in vistos:
            vistos.add(k)
            out.append(list(x))
    return out


def main():
    ahora = time.time()
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for casa in CASAS:
            print("\n=====", casa["nombre"])
            ctx = br.new_context(user_agent=UA, locale="es-ES",
                                 timezone_id="Europe/Madrid",
                                 viewport={"width": 1366, "height": 3000})
            pg = ctx.new_page()
            comps = dict(casa["comp"])
            try:
                comps.update(descubrir(pg, casa["base"]))
            except Exception as e:
                print("   descubrimiento falla", repr(e)[:100])
            partidos = []
            n_ev = 0
            t_casa = time.time()
            for nom, cid in comps.items():
                if time.time() - t_casa > LIMITE_S or n_ev >= MAX_EVENTOS:
                    break
                try:
                    filas = filas_competicion(pg, casa["base"], cid, ahora)
                except Exception as e:
                    print("   competicion", nom, "falla", repr(e)[:80])
                    continue
                print("   ", nom, cid, "->", len(filas), "partidos en ventana")
                for f in filas:
                    if time.time() - t_casa > LIMITE_S or n_ev >= MAX_EVENTOS:
                        break
                    n_ev += 1
                    print("    *", f["c1"], "v", f["c2"],
                          datetime.fromtimestamp(f["inicio"]).strftime("%d/%m %H:%M"), f["h"])
                    eq, tot, jug = leer_evento(ctx, casa["base"], f)
                    print("      equipo:", len(eq), "| totales:", len(tot), "| jugador:", len(jug))
                    partidos.append({
                        "inicio": f["inicio"], "c1": f["c1"], "c2": f["c2"],
                        "equipo": dedup(eq), "total": dedup(tot),
                        "jugador": dedup(jug), "liga": nom,
                    })
            pg.close()
            ctx.close()
            json.dump({"ts": time.time(), "partidos": partidos},
                      open(casa["archivo"], "w", encoding="utf-8"),
                      ensure_ascii=False)
            print("   guardado", casa["archivo"], len(partidos), "partidos")
        br.close()


main()
print("fin", round(time.time() - T0), "s")
