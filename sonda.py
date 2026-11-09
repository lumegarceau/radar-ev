import json, os, re, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("API_FOOTBALL_KEY", "")


def af(ruta, **p):
    q = urllib.parse.urlencode(p)
    rq = urllib.request.Request("https://v3.football.api-sports.io" + ruta + "?" + q,
                                headers={"x-apisports-key": KEY})
    time.sleep(0.3)
    try:
        j = json.load(urllib.request.urlopen(rq, timeout=30))
    except Exception as e:
        print("  fallo", ruta, str(e)[:80])
        return None
    if j.get("errors"):
        print("  error", ruta, j["errors"])
    return j.get("response")


print("=== A. API-Football: casas de cuotas disponibles")
bm = af("/odds/bookmakers") or []
print("casas:", len(bm))
print(sorted(b["name"] for b in bm))
hoy = datetime.now(timezone.utc).date()
fx = af("/fixtures", league=5, season=2026, **{"from": str(hoy), "to": str(hoy + timedelta(days=5))}) or []
print("partidos NL:", len(fx))
pri = None
for f in fx:
    n = f["teams"]["home"]["name"] + " v " + f["teams"]["away"]["name"]
    if "France" in n or "Spain" in n or "England" in n:
        pri = f
        break
pri = pri or (fx[0] if fx else None)
if pri:
    fid = pri["fixture"]["id"]
    print("partido:", pri["teams"]["home"]["name"], "v", pri["teams"]["away"]["name"], fid)
    od = af("/odds", fixture=fid) or []
    for o in od:
        for b in o.get("bookmakers", []):
            print("  casa", b["id"], b["name"], "| mercados:", len(b.get("bets", [])),
                  "|", [x["name"] for x in b.get("bets", [])][:14])
    if not od:
        print("  sin cuotas en API-Football para este partido")

print("\n=== B. Sportium y Marca Apuestas: llamadas internas (JSON) de la web")
from playwright.sync_api import sync_playwright
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CLAVES = ["Francia", "France", "Chequia", "Czech", "Inglaterra", "England", "Croacia", "Italia"]


def prueba(nom, url, texto_enlace=None):
    print("\n---", nom, url)
    resp = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 2400})
        pg = ctx.new_page()

        def on_resp(r):
            try:
                ct = (r.headers.get("content-type") or "")
                if "json" not in ct:
                    return
                b = r.body()
                resp.append((r.url, r.status, len(b), b[:600000].decode("utf-8", "ignore")))
            except Exception:
                pass
        pg.on("response", on_resp)
        try:
            r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            print("estado", r.status if r else None, "| titulo", pg.title()[:70])
            pg.wait_for_timeout(8000)
            for t in ["Aceptar", "Aceptar todo", "Aceptar todas", "Acepto"]:
                try:
                    pg.get_by_text(t, exact=False).first.click(timeout=1500)
                    break
                except Exception:
                    pass
            if texto_enlace:
                try:
                    pg.get_by_text(texto_enlace, exact=False).first.click(timeout=5000)
                    print("clic en", texto_enlace)
                except Exception as e:
                    print("no se pudo pulsar", texto_enlace, repr(e)[:80])
            pg.wait_for_timeout(10000)
            for _ in range(4):
                pg.mouse.wheel(0, 1800)
                pg.wait_for_timeout(1500)
            t = pg.inner_text("body")
            print("texto:", len(t), "| URL final:", pg.url)
            print("muestra:", re.sub(r"\s+", " ", t)[:900])
            hs = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))")
            print("enlaces nations/futbol:", sorted(set(h for h in hs if re.search(r"nations|naciones|futbol", h or "", re.I)))[:12])
        except Exception as e:
            print("FALLO", repr(e)[:160])
        br.close()
    print("respuestas JSON:", len(resp))
    for u, st, n, body in sorted(resp, key=lambda x: -x[2])[:12]:
        print("  ", st, n, u[:160])
    for u, st, n, body in resp:
        hit = [c for c in CLAVES if c in body]
        if hit and n > 1500:
            i = body.find(hit[0])
            print("  >> contiene", hit[:4], "|", u[:140])
            print("     ", re.sub(r"\s+", " ", body[max(0, i - 200):i + 500]))


prueba("Sportium", "https://www.sportium.es/apuestas-deportivas/futbol/nations-league")
prueba("Marca Apuestas", "https://www.marcaapuestas.es/es/", "Nations")
print("\nfin")
