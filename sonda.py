import json, os, re, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
import rvalue as rv

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


hoy = datetime.now(timezone.utc).date()
print("=== A. Convocatorias: tamano de la plantilla y si incluye a los que jugaron")
for tid, nom in [(9, "Espana"), (10, "Inglaterra"), (2, "Francia"),
                 (25, "Alemania"), (777, "Turquia"), (770, "Chequia")]:
    sq = af("/players/squads", team=tid) or []
    ids = set(p["id"] for e in sq for p in e.get("players") or [])
    ult = af("/fixtures", team=tid, last=3) or []
    jug = set()
    for f in ult[:1]:
        st = af("/fixtures/players", fixture=f["fixture"]["id"]) or []
        for e in st:
            if e["team"]["id"] == tid:
                for p in e["players"]:
                    s = p["statistics"][0]
                    if (s["games"].get("minutes") or 0) > 0:
                        jug.add(p["player"]["id"])
    print(nom, "| plantilla:", len(ids), "| jugaron ultimo partido:", len(jug),
          "| de ellos en plantilla:", len(jug & ids))
    if ult:
        ln = af("/fixtures/lineups", fixture=ult[0]["fixture"]["id"]) or []
        print("    alineaciones del ultimo partido:", len(ln))

print("\n=== B. valueodds: partidos de selecciones (12 y 13 nov)")
nl = af("/fixtures", league=5, season=2026,
        **{"from": "2026-11-12", "to": "2026-11-13"}) or []
for fecha in ("2026-11-12", "2026-11-13"):
    lista = rv.listar(fecha)
    print(fecha, "valueodds:", len(lista), "partidos")
    for o in lista:
        n = (o["home_team"].get("name", "") + " v " + o["away_team"].get("name", ""))
        print("    vo:", n, "|", str(o.get("competition") or o.get("league") or "")[:40])
enlazados = 0
for f in nl[:20]:
    dt = datetime.fromisoformat(f["fixture"]["date"])
    lista = rv.listar(f["fixture"]["date"][:10])
    o = rv.emparejar(f["teams"]["home"]["name"], f["teams"]["away"]["name"], dt, lista)
    print("  API:", f["teams"]["home"]["name"], "v", f["teams"]["away"]["name"],
          "->", "SI" if o else "NO emparejado")
    if o and enlazados < 2:
        enlazados += 1
        j = rv.vget("/api/v1/fixtures/" + str(rv.idde(o)) + "/odds?format=compact")
        if j:
            casas = sorted(v.get("name", k) for k, v in (j.get("bookmakers") or {}).items())
            tipos = {}
            for m in j.get("markets") or []:
                t = m.get("type")
                tipos[t] = tipos.get(t, 0) + 1
            print("     casas:", casas)
            print("     mercados:", tipos)

print("\n=== C. Winamax: partidos de selecciones")
try:
    import rwina as rw
    rw.conectar()
    d = rw.pedir("sport:1", "matches", 40)
    ms = d.get("matches", {})
    CL = ["spain", "espana", "france", "francia", "england", "inglaterra",
          "germany", "alemania", "italy", "italia", "croatia", "croacia",
          "belgium", "belgica", "czech", "chequia", "turk"]
    cuenta = {}
    for mid, m in ms.items():
        if not isinstance(m, dict):
            continue
        n = (str(m.get("competitor1Name", "")) + " v " + str(m.get("competitor2Name", "")))
        if any(c in n.lower() for c in CL):
            t = m.get("srTournamentId")
            cuenta[t] = cuenta.get(t, 0) + 1
            print("  ", t, "|", n, "|", m.get("matchStart"))
    print("torneos con selecciones:", cuenta)
    rw.cerrar()
except Exception as e:
    print("FALLO Winamax", repr(e)[:200])

print("\n=== D. Casas nuevas: se pueden leer con navegador?")
from playwright.sync_api import sync_playwright
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
SITIOS = [
    ("Betway NL", "https://betway.es/es/es/sports/grp/soccer"),
    ("Sportium", "https://www.sportium.es/apuestas/futbol"),
    ("Marca Apuestas", "https://www.marcaapuestas.es/es/"),
    ("Retabet", "https://apuestas.retabet.es/futbol"),
    ("Kirolbet", "https://www.kirolbet.es/apuestas/futbol"),
    ("Betfair", "https://www.betfair.es/sport/football"),
]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2000})
    for nom, url in SITIOS:
        pg = ctx.new_page()
        try:
            r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
            pg.wait_for_timeout(9000)
            t = pg.inner_text("body")
            hs = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))")
            nat = sorted(set(h for h in hs if re.search(r"nations|naciones", h or "", re.I)))[:5]
            print(nom, "| estado", r.status if r else None, "| titulo:", pg.title()[:60],
                  "| texto", len(t), "| enlaces", len(hs),
                  "| ligas:", [p for p in ["LaLiga", "Premier", "Bundesliga", "Nations"] if p in t],
                  "| nations:", nat)
            if len(t) < 600:
                print("    cuerpo:", t[:200].replace("\n", " "))
        except Exception as e:
            print(nom, "FALLO", repr(e)[:120])
        pg.close()
    br.close()
print("fin")
