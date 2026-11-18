"""Lee las cuotas de Eldorado Casino (jugador, equipo y totales) con proxy español.
Sale eldorado.json con el mismo formato que juegging.json / betsson.json / betfair.json."""
import json
import os
import re
import time
import unicodedata
import urllib.parse
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

import rbway

ARCH = "eldorado.json"
BASE = "https://eldoradocasino.es"
LIGA0 = BASE + "/sports/soccer-1001/laliga-19000000008?tab=matches"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")
PESADO = ("image", "media", "font")
HORAS = 60
MAX_EVENTOS = 40
MAX_LIGAS = 8
LIMITE_S = 20 * 60
PRIO = re.compile(r"premier|laliga|la liga|segunda|serie a|bundesliga|ligue 1|champions|europa|eredivisie|primeira|conference|copa|championship|liga", re.I)
TORNEOS = {}
STAT_J = {"Remates a Puerta del Jugador": "sot", "Remates Totales del Jugador": "shots",
          "Faltas del Jugador": "fouls", "Entradas del Jugador": "tk"}
GOLES = {"Jugador- Anotará en cualquier momento": 1, "Anota 2 o más": 2}
T0 = time.time()
BYTES = [0]
CUENTA = {}


def proxy():
    raw = "".join(os.environ.get("PROXY_URL", "").split())
    if not raw:
        return None
    if "://" not in raw:
        raw = "http://" + raw
    p = urllib.parse.urlparse(raw)
    return {"server": "%s://%s:%s" % (p.scheme, p.hostname, p.port),
            "username": urllib.parse.unquote(p.username or ""),
            "password": urllib.parse.unquote(p.password or "")}


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower().replace(".", "")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def epoch(v):
    if isinstance(v, (int, float)):
        return float(v) / 1000.0 if v > 1e11 else float(v)
    m = re.search(r"(\d{4})-?(\d{2})-?(\d{2})[T ]?(\d{2}):?(\d{2})", str(v or ""))
    if not m:
        return None
    a = [int(x) for x in m.groups()]
    return datetime(a[0], a[1], a[2], a[3], a[4], tzinfo=timezone.utc).timestamp()


def nombre_j(s):
    s = " ".join(str(s or "").split())
    if ", " in s:
        a, b = s.split(", ", 1)
        return (b + " " + a).strip()
    return s


def cuenta(k, n=1):
    CUENTA[k] = CUENTA.get(k, 0) + n


def parsear(det, c1, c2):
    equipo, total, jug = [], [], {}
    md = det.get("marketsData") or {}
    for m in md.values():
        tn = (m.get("marketTemplateName") or "").strip()
        outs = m.get("outcomes") or []
        st = m.get("marketStatus")
        if st is not None and str(st).lower() not in ("1", "active", "open", "activo"):
            cuenta("mercado_estado_" + str(st))
            continue
        if tn in STAT_J:
            for o in outs:
                sp = str(o.get("specifier") or "")
                c = o.get("odds")
                if not re.match(r"^\d+\+$", sp) or not isinstance(c, (int, float)) or c <= 1:
                    continue
                nom = re.sub(r"\s+\d+\+$", "", str(o.get("name") or ""))
                jug[(STAT_J[tn], nombre_j(nom), int(sp[:-1]))] = float(c)
            continue
        if tn in GOLES:
            for o in outs:
                c = o.get("odds")
                if isinstance(c, (int, float)) and c > 1 and o.get("name"):
                    jug[("goals", nombre_j(o["name"]), GOLES[tn])] = float(c)
            continue
        # equipos y totales: Más/Menos con linea .5
        stat, lado, tot = None, None, False
        mt = None
        if tn == "Remates a Puerta":
            stat, tot = "sot", True
        elif tn.startswith("Faltas Cometidas"):
            stat, tot = "fouls", True
        else:
            mt = re.match(r"^(.+?) - Under/Over Shots on Target$", tn)
            if mt:
                stat = "sot"
            else:
                mt = re.match(r"^(.+?) - Under/Over(?: \{total\})?\s*-?\s*Tiros Totales$", tn)
                if mt:
                    stat = "shots"
                else:
                    mt = re.match(r"^(.+?) - Under/Over - Fouls$", tn)
                    if mt:
                        stat = "fouls"
                    else:
                        mt = re.match(r"^(.+?) - Total de Córners$", tn)
                        if mt:
                            stat = "corners"
            if mt:
                lado = rbway.lado_de(mt.group(1), c1, c2)
                if lado is None:
                    cuenta("equipo_sin_lado")
                    continue
        if stat is None:
            continue
        for o in outs:
            try:
                ln = float(o.get("specifier"))
            except Exception:
                continue
            c = o.get("odds")
            nm = str(o.get("name") or "")
            s = "over" if nm.startswith("Más") else ("under" if nm.startswith("Menos") else None)
            if s is None or not isinstance(c, (int, float)) or c <= 1 or not rbway.medio(ln):
                continue
            if tot:
                total.append([stat, ln, float(c), s])
            else:
                equipo.append([stat, lado, ln, float(c), s])
    for k in jug:
        cuenta("jug_" + k[0])
    return equipo, total, [[k[0], k[1], k[2], c] for k, c in sorted(jug.items())]


def main():
    pr = proxy()
    if not pr:
        print("eldorado: sin PROXY_URL")
        return
    ahora = time.time()
    partidos, vistos = [], set()
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=pr)
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 2500})
        ctx.add_init_script(STEALTH)
        pg = ctx.new_page()
        pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
        ligas, dets = [], {}

        def resp(r):
            try:
                u = r.url
                if "sportsapi" not in u or "json" not in (r.headers.get("content-type") or "").lower():
                    return
                if "sportsapi" in u and "eventview" not in u:
                    tx = r.text()
                    if len(tx) < 3000000:
                        for mt in re.finditer(r'"tournamentId":\s*(\d+),\s*"tournamentName":\s*"([^"]+)"', tx):
                            TORNEOS[mt.group(1)] = mt.group(2)
                if "multi-leagueview" in u:
                    ligas.append(r.text())
                elif "eventview/normalized/" in u:
                    eid = re.search(r"eventview/normalized/(\d+)", u)
                    if eid:
                        d = json.loads(r.text())
                        if len(d.get("marketsData") or {}) >= len((dets.get(eid.group(1)) or {}).get("marketsData") or {}):
                            dets[eid.group(1)] = d
            except Exception:
                pass

        def fin(r):
            try:
                BYTES[0] += r.sizes().get("responseBodySize") or 0
            except Exception:
                pass
        pg.on("response", resp)
        pg.on("requestfinished", fin)

        def ir(url):
            for i in range(3):
                try:
                    pg.goto(url, timeout=90000, wait_until="commit")
                    return True
                except Exception as ex:
                    print("eldorado: reintento goto", i + 1, repr(ex)[:70])
            return False
        if not ir(LIGA0):
            print("eldorado: no abre la web")
            return
        pg.wait_for_timeout(5000)
        try:
            pg.get_by_text("Permitir todas", exact=True).first.click(timeout=4000)
        except Exception:
            pass
        pg.wait_for_timeout(15000)
        eventos = {}

        def recoger(textos):
            for t in textos:
                try:
                    for k, e in (json.loads(t).get("events") or {}).items():
                        if isinstance(e, dict) and e.get("sportId") == 1001:
                            eventos[str(e.get("eventId") or k)] = e
                except Exception:
                    pass
        recoger(ligas)
        print("eldorado: eventos de la primera liga:", len(eventos))
        print("eldorado: torneos vistos en la API:", len(TORNEOS), list(TORNEOS.items())[:25])
        extra = []
        for tid, nm in TORNEOS.items():
            if tid != "19000000008" and PRIO.search(nm):
                extra.append("/sports/soccer-1001/%s-%s?tab=matches" % (slug(nm), tid))
        print("eldorado: ligas extra a probar:", len(extra), extra[:MAX_LIGAS])
        for h in extra[:MAX_LIGAS - 1]:
            n0 = len(ligas)
            try:
                pg.evaluate("(u)=>{history.pushState({},'',u);window.dispatchEvent(new PopStateEvent('popstate',{state:{}}))}", h)
            except Exception:
                continue
            pg.wait_for_timeout(8000)
            recoger(ligas[n0:])
            print("   liga", h[-50:], "-> eventos acumulados:", len(eventos))
        lista = []
        for e in eventos.values():
            t = epoch(e.get("scheduledTimeUtc") or e.get("scheduledTime") or e.get("startDate"))
            if t and ahora - 3600 < t < ahora + HORAS * 3600 and not e.get("live"):
                lista.append((t, e))
        for e in list(eventos.values())[:3]:
            print("eldorado: fecha de ejemplo:", e.get("scheduledTimeUtc"), "|", e.get("scheduledTime"), "|", e.get("startDate"), "| live:", e.get("live"), "->", epoch(e.get("scheduledTimeUtc")))
        print("eldorado: ahora (epoch):", int(ahora))
        lista.sort(key=lambda x: x[0])
        lista = lista[:MAX_EVENTOS]
        print("eldorado: partidos a leer:", len(lista), "| MB hasta aqui: %.1f" % (BYTES[0] / 1048576.0))
        for t, e in lista:
            if time.time() - T0 > LIMITE_S:
                print("eldorado: limite de tiempo, paro")
                break
            eid = str(e["eventId"])
            c1, c2 = e.get("homeTeam"), e.get("awayTeam")
            url = "/sports/event/%s-%s" % (slug(e.get("eventTitle") or ""), eid)
            dets.pop(eid, None)
            try:
                pg.evaluate("(u)=>{history.pushState({},'',u);window.dispatchEvent(new PopStateEvent('popstate',{state:{}}))}", url)
            except Exception:
                pass
            for _ in range(20):
                if eid in dets:
                    break
                pg.wait_for_timeout(1000)
            if eid not in dets:
                print("   sin datos por push, recargo:", c1, "-", c2)
                ir(BASE + url)
                for _ in range(25):
                    if eid in dets:
                        break
                    pg.wait_for_timeout(1000)
            if eid not in dets:
                print("   SIN DATOS:", c1, "-", c2)
                continue
            pg.wait_for_timeout(1500)
            eq, tot, jug = parsear(dets[eid], c1, c2)
            print("   ", c1, "-", c2, "| jugador:", len(jug), "| equipo:", len(eq), "| total:", len(tot))
            if jug or eq or tot:
                partidos.append({"inicio": t, "c1": c1, "c2": c2, "equipo": eq, "total": tot, "jugador": jug})
        br.close()
    print("eldorado: partidos con cuotas:", len(partidos), "| cuotas de jugador:", sum(len(x["jugador"]) for x in partidos),
          "| por tipo:", CUENTA, "| MB: %.1f" % (BYTES[0] / 1048576.0))
    if partidos:
        json.dump({"ts": time.time(), "partidos": partidos}, open(ARCH, "w", encoding="utf-8"), ensure_ascii=False)
        print("eldorado: ejemplo:", partidos[0]["jugador"][:4])
    else:
        print("eldorado: nada que guardar (se conserva el archivo anterior)")


main()
