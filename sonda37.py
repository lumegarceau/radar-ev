"""Sonda Betinia (Altenar), con proxy espanol: que llamadas devuelven partidos y mercados de jugador,
y si esas llamadas se pueden repetir SIN navegador (barato) usando solo el proxy."""
import json
import os
import re
import time
import urllib.parse
import urllib.request

from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
PAL = re.compile(r"player|jugador|tiros?|remates?|shots?|fouls?|faltas?|tarjetas?|cards?|tackles?|offsides?", re.I)
START = "https://betinia.es/es/sport?sportRoutingParams=page~sport__sportId~66"


def proxy():
    raw = "".join(os.environ.get("PROXY_URL", "").split())
    if not raw:
        return None
    if "://" not in raw:
        raw = "http://" + raw
    pu = urllib.parse.urlparse(raw)
    return {"server": "%s://%s:%s" % (pu.scheme, pu.hostname, pu.port),
            "username": urllib.parse.unquote(pu.username or ""),
            "password": urllib.parse.unquote(pu.password or ""), "raw": raw}


def main():
    pr = proxy()
    if not pr:
        print("sin PROXY_URL")
        return
    llamadas = []   # (url, status, texto)
    with sync_playwright() as p:
        br = p.chromium.launch(proxy={k: v for k, v in pr.items() if k != "raw"})
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 2500})
        pg = ctx.new_page()
        pg.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())

        def resp(r):
            if "biahosted.com/api/" in r.url:
                try:
                    llamadas.append((r.url, r.status, r.text()))
                except Exception:
                    pass
        pg.on("response", resp)
        print("== pagina de futbol")
        pg.goto(START, timeout=60000, wait_until="domcontentloaded")
        for tx in ("Aceptar todas", "Aceptar todo", "Aceptar"):
            try:
                b = pg.get_by_text(tx, exact=False).first
                if b.count():
                    b.click(timeout=3000)
                    break
            except Exception:
                pass
        pg.wait_for_timeout(15000)
        print("titulo:", pg.title()[:70])
        hrefs = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))")
        ev = [h for h in hrefs if h and re.search(r"event", h, re.I)]
        print("enlaces con 'event':", ev[:6])
        print("== llamadas a la API de Altenar")
        vistas = {}
        for u, st, t in llamadas:
            ruta = urllib.parse.urlparse(u).path.split("/api/")[-1]
            vistas.setdefault(ruta, []).append((st, len(t), u))
        for ruta, v in vistas.items():
            print(" ", ruta, "| veces", len(v), "| http", v[0][0], "| bytes", v[0][1])
        # llamada con mas partidos
        mejor = None
        for u, st, t in llamadas:
            if st == 200 and "event" in u.lower():
                try:
                    j = json.loads(t)
                except Exception:
                    continue
                evs = j.get("events") if isinstance(j, dict) else None
                if evs and (not mejor or len(evs) > len(mejor[1])):
                    mejor = (u, evs, j)
        if mejor:
            u, evs, j = mejor
            print("== llamada de partidos:", u[:230])
            print("partidos:", len(evs), "| claves del partido:", sorted(evs[0].keys())[:25])
            for e in evs[:4]:
                print("  ", e.get("name"), "| id", e.get("id"), "| inicio", e.get("startDate"), "| liga", e.get("champName") or e.get("champId"))
            print("claves de la respuesta:", sorted(j.keys())[:15])
        else:
            print("no he visto ninguna llamada de partidos con 'events'")
        # detalle de un partido: abrir el primer enlace de partido
        det = None
        if ev:
            try:
                pg.goto(ev[0] if ev[0].startswith("http") else "https://betinia.es" + ev[0], timeout=60000, wait_until="domcontentloaded")
                pg.wait_for_timeout(15000)
            except Exception as e:
                print("fallo al abrir partido:", repr(e)[:80])
        for u, st, t in llamadas[::-1]:
            if "geteventdetails" in u.lower() or "eventdetails" in u.lower():
                det = (u, st, t)
                break
        if det:
            u, st, t = det
            print("== detalle de partido:", u[:230], "| http", st, "| bytes", len(t))
            nombres = sorted(set(m.group(0).lower() for m in PAL.finditer(t)))
            print("palabras de jugador en el detalle:", nombres[:15])
            try:
                j = json.loads(t)
                mk = j.get("markets") or []
                tipos = sorted(set(str(m.get("name")) for m in mk))
                print("mercados:", len(mk), "| con palabras de jugador:", [x for x in tipos if PAL.search(x)][:25])
                print("ejemplo de mercado de jugador:", json.dumps([m for m in mk if PAL.search(str(m.get('name')))][:1], ensure_ascii=False)[:600])
            except Exception as e:
                print("no se pudo leer el detalle:", repr(e)[:80])
        else:
            print("no he visto llamada de detalle de partido")
        br.close()
    # repetir una llamada de partidos SIN navegador, solo con el proxy
    if mejor:
        u = mejor[0]
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": pr["raw"], "https": pr["raw"]}))
        rq = urllib.request.Request(u, headers={"User-Agent": UA, "Origin": "https://betinia.es", "Referer": "https://betinia.es/"})
        try:
            r = op.open(rq, timeout=40)
            b = r.read()
            print("== SIN navegador: http", r.status, "| bytes", len(b))
        except Exception as e:
            print("== SIN navegador: falla", repr(e)[:150])


main()
