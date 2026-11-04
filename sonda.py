import json
import re
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SITIOS = {
    "Betfair": [
        "https://www.betfair.es/sport/football",
        "https://www.betfair.es/sport",
    ],
    "Betway": [
        "https://betway.es/es/sports/cpn/soccer/1",
        "https://betway.es/es/sports",
        "https://betway.es/",
    ],
}
CLAVES = re.compile(
    r"c[oó]rner|esquina|corner|tarjeta|card|remate|tiros|shots|faltas",
    re.I)


def http(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        r = urllib.request.urlopen(req, timeout=20)
        t = r.read(4000).decode("utf-8", "ignore")
        return r.status, t[:150].replace("\n", " ")
    except Exception as e:
        return "ERR", repr(e)[:150]


def sonda(pw, nombre, urls):
    print("=" * 60)
    print(nombre)
    for u in urls:
        print("HTTP directo", u, http(u))
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES",
                         timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 900})
    pg = ctx.new_page()
    vistos = []

    def resp(r):
        try:
            ct = r.headers.get("content-type", "")
            if "json" not in ct:
                return
            cuerpo = r.text()
            vistos.append((r.url, r.status, len(cuerpo),
                           bool(CLAVES.search(cuerpo)), cuerpo[:120]))
        except Exception:
            pass

    pg.on("response", resp)
    for u in urls:
        try:
            r = pg.goto(u, timeout=45000, wait_until="domcontentloaded")
            pg.wait_for_timeout(9000)
            print("NAVEGADOR", u, "->", r.status if r else None,
                  pg.url[:100])
            print("titulo:", pg.title()[:100])
            txt = pg.inner_text("body")[:300].replace("\n", " | ")
            print("texto:", txt)
            if r and r.status == 200 and len(vistos) > 3:
                break
        except Exception as e:
            print("fallo", u, repr(e)[:200])
    print("JSON recibidos:", len(vistos))
    vistos.sort(key=lambda v: (not v[3], -v[2]))
    for v in vistos[:25]:
        print(" ", "MERCADOS" if v[3] else "-", v[1], v[2], v[0][:140])
        if v[3]:
            print("     ", v[4])
    br.close()


with sync_playwright() as pw:
    for n, u in SITIOS.items():
        try:
            sonda(pw, n, u)
        except Exception as e:
            print(n, "fallo general", repr(e)[:200])
print("fin")
