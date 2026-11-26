"""Sonda 41: que torneos de Winamax son Libertadores, Arabia, Escocia, Suiza, Austria, Mexico, Grecia y si traen props de jugador."""
import re
import time
import rwina as rw

rw.conectar()
d = rw.pedir("sport:1", "matches", 40)
ms = d.get("matches", {})
print("claves de la respuesta:", [k for k in d.keys()])
tor = d.get("tournaments", {}) or {}
cat = d.get("categories", {}) or {}
ahora = time.time()
por = {}
for mid, m in ms.items():
    if not isinstance(m, dict) or m.get("status") != "PREMATCH":
        continue
    ini = m.get("matchStart") or 0
    if ini > ahora + 10 * 86400:
        continue
    por.setdefault((m.get("srTournamentId"), m.get("tournamentId")), []).append((ini, mid, m))
CLAVE = re.compile(r"libertad|sudamerican|arabia|saud|escoc|scot|suiza|swiss|austria|m[eé]xico|liga mx|grecia|greece|super ?league|premiership|pro league|bundesliga", re.I)
print("\nTORNEOS con partidos en 10 dias:", len(por))
sel = []
for (sr, tid), lst in sorted(por.items(), key=lambda a: str(a[0])):
    t = tor.get(str(tid), {}) if isinstance(tor, dict) else {}
    c = cat.get(str(t.get("categoryId")), {}) if isinstance(cat, dict) else {}
    nom = "%s / %s" % (c.get("categoryName") or c.get("name") or "?", t.get("tournamentName") or t.get("name") or "?")
    ej = ""
    marca = "  <<<<" if (CLAVE.search(nom) or (nom.startswith("?") and len(sel) < 40 and len(lst) >= 2)) else ""
    print("%s | tid %s | %s | %d partidos | ej: %s%s" % (sr, tid, nom, len(lst), " | ".join(str(x[2].get("title")) for x in lst[:3]), marca))
    if marca:
        sel.append((sr, nom, lst))
print("\nMUESTRA DE PROPS por torneo marcado")
for sr, nom, lst in sel:
    lst.sort()
    ini, mid, m = lst[0]
    try:
        dd = rw.pedir("match:" + str(mid), "bets", 25)
    except Exception as e:
        print(sr, nom, "fallo", repr(e)[:80])
        rw.conectar()
        continue
    bets = dd.get("bets", {}) or {}
    tit = [str(b.get("betTitle", "")) for b in bets.values() if isinstance(b, dict)]
    pj = [t for t in tit if re.match(r"^(Realiza|Comete|Recibe)", t)]
    eq = [t for t in tit if re.match(r"^N[uú]mero", t)]
    print("%s | %s | %s | mercados %d | jugador %d | equipo %d" % (sr, nom, m.get("title"), len(tit), len(pj), len(eq)))
rw.cerrar()
