"""Lee las cuotas de Juegging (mismas que Kirolbet) con Playwright y guarda
juegging.json con el mismo formato que sportium.json / marca.json."""
import json
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = "https://apuestas.juegging.es"
ARCHIVO = "juegging.json"
MADRID = ZoneInfo("Europe/Madrid")
HORAS = 80
LIMITE_S = 22 * 60
MAX_EVENTOS = 45
T0 = time.time()
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
# listados donde buscar partidos (competiciones fijas + portada + proximos)
LISTADOS = ["/esp/Sport", "/esp/Sport/Hoy/ProximosEventos",
            "/esp/Sport/Competicion/1", "/esp/Sport/Competicion/341",
            "/esp/Sport/Competicion/3"]
PESTANAS = ["REMATES A PUERTA", "FALTAS", "PARADAS"]
NUM = re.compile(r"^\d+[.,]\d+$")
IGNORADOS = set()


def a_float(s):
    return float(s.replace(",", "."))


def nombre_normal(s):
    """'Raya Martín, David' -> 'David Raya Martín'; sin coma se deja igual."""
    s = s.strip()
    if "," in s:
        ap, no = s.split(",", 1)
        return (no.strip() + " " + ap.strip()).strip()
    return s


def clasificar(desc):
    """'Player remates a puerta +1.5' -> ('sot', 2)."""
    m = re.match(r"^Player\s+(.+?)\s*\+\s*(\d+(?:[.,]\d+)?)\s*$", desc, re.I)
    if not m:
        return None
    t = re.sub(r"\s+", " ", m.group(1).strip().lower())
    lin = a_float(m.group(2))
    if abs((lin % 1) - 0.5) > 1e-9:
        return None
    n = int(lin + 0.5)
    # solo los nombres EXACTOS: hay variantes (1a parte, dentro del area...)
    # con otras cuotas que no se deben mezclar con estas
    EXACTOS = {"remates a puerta": "sot", "remates": "shots",
               "faltas cometidas": "fouls", "faltas recibidas": "drawn",
               "paradas portero": "saves"}
    if t in EXACTOS:
        return (EXACTOS[t], n)
    return None


def parsear_pestana(texto):
    """Devuelve (filas, resumen). Estructura: PARTICIPANTES, una linea por
    jugador, y luego bloques 'Player xxx +L' con una cuota por jugador."""
    lineas = [x.strip() for x in texto.split("\n") if x.strip()]
    filas = []
    resumen = {}
    i = 0
    n = len(lineas)
    nombres = []
    while i < n:
        l = lineas[i]
        if l.upper() == "PARTICIPANTES":
            nombres = []
            i += 1
            while i < n and lineas[i].upper() != "PARTICIPANTES" \
                    and not lineas[i].startswith("Player ") \
                    and not lineas[i].startswith("Total ") \
                    and not lineas[i].upper().startswith("MI BOLETO"):
                if lineas[i].upper() != "VER MÁS":
                    nombres.append(lineas[i])
                i += 1
            continue
        if l.startswith("Player ") and nombres:
            k = clasificar(l)
            vals = lineas[i + 1:i + 1 + len(nombres)]
            ok = len(vals) == len(nombres) and all(NUM.match(v) or v == "-" for v in vals)
            if not ok:
                resumen[l] = "no_cuadra(%d nombres)" % len(nombres)
                i += 1
                continue
            if k:
                stat, nn = k
                c = 0
                for nom, v in zip(nombres, vals):
                    if v != "-":
                        filas.append((stat, nombre_normal(nom), nn, a_float(v)))
                        c += 1
                resumen[l] = c
            else:
                resumen[l] = "ignorado"
                IGNORADOS.add(re.sub(r"\s*\+\s*\d+(?:[.,]\d+)?\s*$", "", l))
            i += 1 + len(nombres)
            continue
        i += 1
    return filas, resumen


def inicio_de(dt):
    """'12/11/2026 20:45:00' (hora de Madrid) -> timestamp."""
    try:
        d = datetime.strptime(dt.strip(), "%d/%m/%Y %H:%M:%S").replace(tzinfo=MADRID)
        return d.timestamp()
    except Exception:
        return None


def equipos_de(des):
    p = re.split(r"\s+vs\.?\s+", des, flags=re.I)
    return (p[0].strip(), p[1].strip()) if len(p) == 2 else (None, None)


def main():
    from playwright.sync_api import sync_playwright

    def texto(pg):
        return pg.inner_text("body")

    def cargar(pg, url, minimo=3000):
        for _ in range(3):
            try:
                pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print("   goto falla:", repr(e)[:80])
                continue
            for _ in range(10):
                pg.wait_for_timeout(3500)
                try:
                    if len(texto(pg)) > minimo:
                        return True
                except Exception:
                    pass
        return False

    JS_EV = """()=>Array.from(document.querySelectorAll('a[href*="/Sport/Evento/"]'))
      .map(a=>a.getAttribute('href'))"""
    JS_META = """()=>{const e=document.querySelector('[data-ideve][dt][des]');
      return e?{dt:e.getAttribute('dt'),des:e.getAttribute('des'),sct:e.getAttribute('sct')}:null}"""
    JS_TAB = """(t)=>{const e=Array.from(document.querySelectorAll('a')).find(x=>(x.innerText||'').trim().toUpperCase()===t);
      if(e){e.click();return true}return false}"""

    ahora = time.time()
    partidos = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 4000})
        pg = ctx.new_page()
        eventos = []
        for ruta in LISTADOS:
            if not cargar(pg, BASE + ruta, 1500):
                print("   listado no carga:", ruta)
                continue
            try:
                hs = pg.evaluate(JS_EV)
            except Exception:
                hs = []
            nuevos = [h for h in dict.fromkeys(hs) if h not in eventos]
            print("   listado", ruta, "->", len(hs), "enlaces,", len(nuevos), "nuevos")
            eventos += nuevos
        print("   eventos candidatos:", len(eventos))
        vistos = 0
        hechos = set()
        for h in eventos:
            if time.time() - T0 > LIMITE_S or vistos >= MAX_EVENTOS:
                print("   limite alcanzado")
                break
            url = BASE + h if h.startswith("/") else h
            if not cargar(pg, url, 5000):
                continue
            try:
                meta = pg.evaluate(JS_META)
            except Exception:
                meta = None
            if not meta:
                continue
            ini = inicio_de(meta["dt"])
            c1, c2 = equipos_de(meta["des"])
            if not ini or not c1 or ini < ahora - 3600 or ini > ahora + HORAS * 3600:
                continue
            if (c1, c2, round(ini)) in hechos:
                continue  # el mismo partido aparece con dos enlaces
            hechos.add((c1, c2, round(ini)))
            tabs_ok = []
            filas = []
            for tab in PESTANAS:
                try:
                    if not pg.evaluate(JS_TAB, tab):
                        continue
                    pg.wait_for_timeout(5000)
                    f, res = parsear_pestana(texto(pg))
                    tabs_ok.append(tab)
                    filas += f
                except Exception as e:
                    print("      pestana", tab, "falla", repr(e)[:60])
            if not tabs_ok:
                continue  # no es futbol con props
            vistos += 1
            # sin duplicados (el mismo jugador/linea aparece una sola vez)
            uniq = {}
            for stat, nom, nn, c in filas:
                uniq[(stat, nom, nn)] = c
            jug = [[s, nom, nn, c] for (s, nom, nn), c in uniq.items()]
            print("    *", c1, "v", c2, datetime.fromtimestamp(ini, MADRID).strftime("%d/%m %H:%M"),
                  "|", meta["sct"], "| pestanas", len(tabs_ok), "| jugador:", len(jug))
            partidos.append({"inicio": ini, "c1": c1, "c2": c2, "equipo": [], "total": [],
                             "jugador": jug, "liga": meta["sct"], "fuente": "Juegging"})
        br.close()
    print("   mercados ignorados (variantes):", sorted(IGNORADOS)[:25])
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump({"ts": time.time(), "partidos": partidos}, f, ensure_ascii=False)
    print("guardado", ARCHIVO, len(partidos), "partidos")
    print("fin", round(time.time() - T0), "s")


if __name__ == "__main__":
    main()
