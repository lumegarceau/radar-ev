import json, os, time, urllib.parse, urllib.request
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


print("=== 1. valueodds: TODAS las casas que devuelve (antes de filtrar)")
hoy = datetime.now(timezone.utc).date()
cuenta = {}
vistos = 0
for d in range(0, 4):
    fecha = str(hoy + timedelta(days=d))
    lista = rv.listar(fecha)
    print(fecha, "partidos en valueodds:", len(lista))
    for o in lista[:14]:
        j = rv.vget("/api/v1/fixtures/" + str(rv.idde(o)) + "/odds?format=compact")
        if not j:
            continue
        vistos += 1
        for k, v in (j.get("bookmakers") or {}).items():
            n = v.get("name", k)
            cuenta[n] = cuenta.get(n, 0) + 1
print("partidos revisados:", vistos)
for n, c in sorted(cuenta.items(), key=lambda kv: -kv[1]):
    marca = "OK " if rv.canon(n) else "-- "
    print("  ", marca, n, c)

print("\n=== 2. API-Football: Nations League")
r = af("/leagues", search="Nations League") or []
for x in r:
    l = x["league"]
    print("liga", l["id"], l["name"], l["type"])
    for s in x["seasons"][-3:]:
        c = s["coverage"]
        print("   temporada", s["year"], s["start"], s["end"],
              "| stats jugadores:", c["fixtures"]["statistics_players"],
              "| alineaciones:", c["fixtures"]["lineups"],
              "| plantillas:", c.get("players"), "| cuotas:", c.get("odds"))
ids = [x["league"]["id"] for x in r if "UEFA" in x["league"]["name"]
       or x["league"]["id"] == 5]
for lid in ids[:3]:
    for temp in (2026, 2025):
        fx = af("/fixtures", league=lid, season=temp,
                **{"from": str(hoy), "to": str(hoy + timedelta(days=40))}) or []
        print("liga", lid, "temporada", temp, "partidos proximos 40 dias:", len(fx))
        for f in fx[:12]:
            print("   ", f["fixture"]["date"][:16], f["teams"]["home"]["name"], "v",
                  f["teams"]["away"]["name"], "| id", f["fixture"]["id"],
                  "| equipo ids", f["teams"]["home"]["id"], f["teams"]["away"]["id"])
        if fx:
            tid = fx[0]["teams"]["home"]["id"]
            sq = af("/players/squads", team=tid) or []
            print("   plantilla", fx[0]["teams"]["home"]["name"], ":",
                  [(p["name"], p.get("position")) for p in (sq[0]["players"][:8] if sq else [])])
            ps = af("/players", team=tid, season=temp, league=lid) or []
            print("   /players con liga", lid, ":", len(ps))
            if ps:
                p0 = ps[0]
                print("   ejemplo:", p0["player"]["name"],
                      [(s["league"]["name"], s["games"]["appearences"])
                       for s in p0["statistics"][:4]])
            break

print("\n=== 3. Ultimos partidos jugados de una seleccion (para historial)")
r = af("/fixtures", team=9, last=8) or []   # 9 = Espana
for f in r:
    print("  ", f["fixture"]["date"][:10], f["league"]["name"], "|",
          f["teams"]["home"]["name"], f["goals"]["home"], "-", f["goals"]["away"],
          f["teams"]["away"]["name"], "| id", f["fixture"]["id"])
if r:
    fid = r[0]["fixture"]["id"]
    st = af("/fixtures/players", fixture=fid) or []
    print("  estadisticas de jugadores del ultimo partido:", len(st), "equipos")
    if st:
        print("   ejemplo:", st[0]["players"][0]["player"]["name"],
              st[0]["players"][0]["statistics"][0]["shots"])
    ln = af("/fixtures/lineups", fixture=fid) or []
    print("  alineaciones disponibles:", len(ln))
print("fin")
