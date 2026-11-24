"""Lee las cuotas de jugador de Betfair (remates, remates a puerta, faltas) con proxy español.
Sale betfair.json con el mismo formato que juegging.json / betsson.json."""
import json
import os
import random
import re
import time
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

ARCH = "betfair.json"
LISTADO = "https://www.betfair.es/apuestas/f%C3%BAtbol/s-1"
BASE = "https://www.betfair.es/apuestas/"
_F = BASE + "f%C3%BAtbol/"
# Paginas de cada competicion (en orden de prioridad). El listado general se lee al final.
COMPETICIONES = [_F + x for x in (
    "uefa-champions-league/c-228", "uefa-europa-league/c-2005", "la-liga-espa%C3%B1ola/c-117",
    "espa%C3%B1a-segunda-divisi%C3%B3n/c-12204313", "premier-league-inglesa/c-10932509",
    "inglaterra-sky-bet-championship/c-7129730", "serie-a-italiana/c-81",
    "bundesliga-alemana/c-59", "ligue-1-francesa/c-55", "portugal-primeira-liga/c-99",
    "eredivisie-holandesa/c-9404054", "b%C3%A9lgica-pro-league/c-89979",
    "superliga-turca/c-194215", "dinamarca-superliga/c-23", "serie-a-brasil/c-13",
    "argentina-primera-divisi%C3%B3n/c-67387", "liga-a-de-naciones-de-la-uefa/c-12209069")]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MAD = ZoneInfo("Europe/Madrid")
HORAS = 40
MAX_EVENTOS = 60
LIMITE_S = 25 * 60
PESADO = ("image", "media", "font")
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")
GRUPOS = re.compile(r"tiros? a puerta|tiros del jugador|jugador que comete falta", re.I)
TIPOS = [(re.compile(r"^PLAYER_TO_HAVE_(\d+)_OR_MORE_SHOTS_ON_TARGET_STAR_SUB$"), "sot"),
         (re.compile(r"^PLAYER_TO_HAVE_(\d+)_OR_MORE_SHOTS_STAR_SUB$"), "shots"),
         (re.compile(r"^PLAYER_TO_COMMIT_(\d+)_OR_MORE_FOULS_STAR_SUB$"), "fouls")]
CLAVES_NOMBRE = ("runnerName", "name", "selectionName", "displayName", "participantName", "title", "label")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6, "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}
T0 = time.time()
BYTES = [0]
AVISOS = {"tipos": set(), "sin_nombre": 0, "muestra": None}


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


def caminar(x, f, prof=0):
    if prof > 25:
        return
    if isinstance(x, dict):
        f(x)
        for v in x.values():
            caminar(v, f, prof + 1)
    elif isinstance(x, list):
        for v in x:
            caminar(v, f, prof + 1)


def grupos_de(textos):
    """[(titulo, parte, urn de tarjeta)] de los mercados de la pagina del partido."""
    out, vistos = [], set()

    def f(d):
        if d.get("__typename") == "PebbleCardGroup":
            t = ((d.get("pebbleCardGroupTitle") or {}).get("translated")) or ""
            for e in ((d.get("partials") or {}).get("edges") or []):
                u = (e.get("node") or {}).get("urn")
                if u and u not in vistos:
                    vistos.add(u)
                    out.append((t, e.get("name"), u))
    for t in textos:
        try:
            caminar(json.loads(t), f)
        except Exception:
            pass
    return out


def id_de(r):
    sid = r.get("selectionId")
    if sid is None:
        for k in ("runnerURN", "urn"):
            u = str(r.get(k) or "")
            if "/" in u:
                sid = u.rsplit("/", 1)[-1]
                break
    return str(sid) if sid is not None else None


def nombre_de(r):
    for k in CLAVES_NOMBRE:
        v = r.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    hallado = []

    def f(d):
        if not hallado:
            for k in CLAVES_NOMBRE:
                v = d.get(k)
                if isinstance(v, str) and v.strip():
                    hallado.append(v.strip())
                    return
    caminar(r, f)
    return hallado[0] if hallado else None


def cuotas_de(cards):
    """De las GridCard saca {(stat, jugador, n): cuota}."""
    jug = {}
    for c in cards:
        if not c or c.get("__typename") != "GridCard":
            continue
        for it in c.get("markets") or []:
            mk = it.get("market") or {}
            tipo = str(mk.get("marketType") or "")
            hit = None
            for rx, stat in TIPOS:
                m = rx.match(tipo)
                if m:
                    hit = (stat, int(m.group(1)))
                    break
            if not hit:
                AVISOS["tipos"].add(tipo)
                continue
            nom = {}
            for src in (mk.get("runners"), c.get("runners")):
                for r in src or []:
                    if isinstance(r, dict):
                        sid, n = id_de(r), nombre_de(r)
                        if sid and n:
                            nom.setdefault(sid, n)
            for r in (mk.get("liveData") or {}).get("runners") or []:
                if r.get("runnerStatus") != "ACTIVE":
                    continue
                n = nom.get(id_de(r))
                if not n:
                    AVISOS["sin_nombre"] += 1
                    if AVISOS["muestra"] is None and (mk.get("runners") or [None])[0] is not None:
                        AVISOS["muestra"] = json.dumps((mk.get("runners") or [None])[0], ensure_ascii=False)[:500]
                    continue
                try:
                    q = float((r.get("odds") or {}).get("decimal"))
                except Exception:
                    continue
                if q > 1.0:
                    k = (hit[0], n, hit[1])
                    if q > jug.get(k, 0):
                        jug[k] = q
    return jug


def inicio_de(txt, ancla):
    """Epoch UTC del partido a partir del texto 'Hoy, 18:00' / 'Mañana, 18:00' / '14 nov, 20:45' / '14/11 20:45'."""
    k = txt.find(ancla) if ancla else 0
    t = txt[max(0, k):max(0, k) + 400] if k >= 0 else txt[:3000]
    ahora = datetime.now(MAD)
    m = re.search(r"\b(Hoy|Mañana),?\s+(\d{1,2}):(\d{2})", t)
    if m:
        d = ahora.date() + timedelta(days=1 if m.group(1) == "Mañana" else 0)
        h, mi = int(m.group(2)), int(m.group(3))
    else:
        m = re.search(r"\b(\d{1,2})\s+(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)\w*\.?,?\s+(\d{1,2}):(\d{2})", t, re.I)
        if m:
            mes = MESES[m.group(2).lower()]
            dia = int(m.group(1))
        else:
            m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/\d{2,4})?,?\s+(\d{1,2}):(\d{2})", t)
            if not m:
                return None
            dia, mes = int(m.group(1)), int(m.group(2))
        yr = ahora.year + (1 if mes < ahora.month - 6 else 0)
        try:
            d = datetime(yr, mes, dia).date()
        except ValueError:
            return None
        h, mi = int(m.group(3)), int(m.group(4))
    return datetime(d.year, d.month, d.day, h, mi, tzinfo=MAD).timestamp()


def leer_partido(br, url_rel):
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 3000})
    ctx.add_init_script(STEALTH)
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
    got, reqs = [], []

    def resp(r):
        try:
            if "bff-gql" in r.url and "json" in (r.headers.get("content-type") or ""):
                got.append(r.text())
        except Exception:
            pass

    def req(r):
        try:
            if "bff-gql" in r.url and r.method == "POST" and "documentId" in (r.post_data or ""):
                reqs.append((r.url, r.all_headers(), r.post_data))
        except Exception:
            pass

    def fin(rq):
        try:
            sz = rq.sizes()
            BYTES[0] += (sz.get("responseBodySize") or 0) + (sz.get("responseHeadersSize") or 0)
        except Exception:
            pass
    pg.on("response", resp)
    pg.on("request", req)
    pg.on("requestfinished", fin)
    try:
        pg.goto(BASE + url_rel, timeout=60000, wait_until="domcontentloaded")
        for _ in range(8):
            pg.wait_for_timeout(4000)
            if "momento" not in pg.title().lower():
                break
        sel = []
        for _ in range(8):
            pg.wait_for_timeout(3000)
            sel = [g for g in grupos_de(got) if GRUPOS.search(g[0])]
            if sel and reqs:
                break
        if not sel or not reqs:
            ctx.close()
            return None, "sin mercados de jugador (respuestas %d)" % len(got)
        titulo = pg.title()
        cuerpo = " ".join(pg.inner_text("body").split())
        url, hd, post0 = reqs[0]
        base = json.loads(post0)
        hdr = {k: v for k, v in hd.items() if not k.startswith(":") and k not in (
            "content-length", "host", "cookie", "origin", "referer", "user-agent", "accept-encoding", "connection")}
        cards = []
        for i in range(0, len(sel), 5):
            b = dict(base)
            v = dict(base["variables"])
            v["urn"] = [g[2] for g in sel[i:i + 5]]
            b["variables"] = v
            r = pg.evaluate("""async ([u,h,b])=>{const r=await fetch(u,{method:'POST',headers:h,body:b,credentials:'include'});return {s:r.status,t:await r.text()}}""",
                            [url, hdr, json.dumps(b)])
            BYTES[0] += len(r["t"]) // 4
            if r["s"] == 200:
                try:
                    cards += (json.loads(r["t"]).get("data") or {}).get("Cards") or []
                except Exception:
                    pass
        ctx.close()
        return (titulo, cuerpo, cuotas_de(cards)), None
    except Exception as ex:
        try:
            ctx.close()
        except Exception:
            pass
        return None, repr(ex)[:120]


def main():
    pr = proxy()
    if not pr:
        print("betfair: falta PROXY_URL")
        return
    partidos = []
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=pr)
        vistos = set()
        grupos = []
        desafios = 0
        diag_hecho = False
        # el listado general primero (el que ya funcionaba), luego cada competicion
        for n_pag, cu in enumerate([LISTADO] + COMPETICIONES):
            nom_c = urllib.parse.unquote(cu).rstrip("/").split("/")[-2] if "/c-" in cu else "listado general"
            if n_pag:
                time.sleep(random.uniform(15, 30))
            # contexto nuevo por pagina: sin cookies ni huella de la anterior
            ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                                 viewport={"width": 1366, "height": 2500})
            ctx.add_init_script(STEALTH)
            pg = ctx.new_page()
            pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
            bag = []
            pg.on("response", lambda r: bag.append(r.text()) if ("bff-gql" in r.url and "json" in (r.headers.get("content-type") or "")) else None)
            pg.on("requestfinished", lambda rq: BYTES.__setitem__(0, BYTES[0] + ((rq.sizes().get("responseBodySize") or 0) if True else 0)))
            estado = None
            try:
                rp = pg.goto(cu, timeout=60000, wait_until="domcontentloaded")
                estado = rp.status if rp else None
                # si sale la verificacion de seguridad, se le da tiempo a resolverse sola
                for _ in range(6):
                    if "un momento" not in pg.title().lower():
                        break
                    pg.wait_for_timeout(5000)
                pg.wait_for_timeout(12000)
            except Exception as e_c:
                print("betfair: competicion", nom_c, "falla:", repr(e_c)[:70])
                ctx.close()
                continue
            reto = "un momento" in pg.title().lower()
            urls = []
            for t in list(bag):
                t = t.replace("\\/", "/")
                for u in re.findall(r'f(?:%C3%BA|ú|\\u00fa)tbol/[^"\\?\s]+/e-\d+', t):
                    u = u.replace("fútbol", "f%C3%BAtbol", 1).replace("f\\u00fatbol", "f%C3%BAtbol", 1)
                    if u not in urls and u not in vistos:
                        urls.append(u)
                        vistos.add(u)
            n_gql = len(urls)
            try:
                hrefs = pg.evaluate("()=>Array.from(document.querySelectorAll('a[href]')).map(a=>a.getAttribute('href'))")
            except Exception:
                hrefs = []
            n_e = 0
            for h in hrefs:
                m = re.search(r'f(?:%C3%BA|ú)tbol/[^"\\?#]+/e-\d+', h or "")
                if m:
                    n_e += 1
                    u = m.group(0).replace("fútbol", "f%C3%BAtbol", 1)
                    if u not in urls and u not in vistos:
                        urls.append(u)
                        vistos.add(u)
            print("betfair: competicion", nom_c, "->", len(urls), "partidos nuevos",
                  "| http", estado, "| reto" if reto else "| ok", "| gql", len(bag), "resp,", n_gql, "partidos | enlaces", len(hrefs), "(a partidos:", n_e, ")")
            if not urls and not reto and not diag_hecho:
                diag_hecho = True
                try:
                    for t in bag[:6]:
                        ms = [m.start() for m in re.finditer(r"e-\d{6,}", t)][:2]
                        print("     DIAG gql", len(t), "bytes | claves:", re.findall(r'"([A-Za-z_]{3,20})":', t)[:25],
                              "| contexto e-ID:", [t[max(0, k - 70):k + 20] for k in ms])
                    print("     DIAG enlaces de ejemplo:", [h for h in hrefs if h and ("tbol" in h or "/e-" in h)][:8])
                    print("     DIAG texto:", " ".join(pg.inner_text("body").split())[300:700])
                except Exception as e_dg:
                    print("     DIAG fallo:", repr(e_dg)[:80])
            ctx.close()
            if reto:
                desafios += 1
                if desafios >= 2:
                    print("betfair: 2 verificaciones de seguridad seguidas, se corta para no gastar proxy")
                    break
            else:
                desafios = 0
            grupos.append(urls)
        leidos = 0
        for urls in grupos:
            lejos = 0
            for u in urls:
                if leidos >= MAX_EVENTOS or time.time() - T0 > LIMITE_S:
                    break
                leidos += 1
                res, err = leer_partido(br, u)
                if not res and "respuestas 0" in str(err):
                    res, err = leer_partido(br, u)
                nombre = urllib.parse.unquote(u).split("/")[-2]
                if not res:
                    print("  ", nombre, "-> falla:", err)
                    continue
                titulo, cuerpo, jug = res
                t = titulo.replace("Apuestas", "", 1).split("»")[0].strip()
                eq = [x.strip() for x in t.split(" - ")] if " - " in t else []
                if len(eq) != 2:
                    print("  ", nombre, "-> no saco los equipos de:", titulo[:60])
                    continue
                ini = inicio_de(cuerpo, eq[0] + " - " + eq[1])
                if not ini:
                    k = cuerpo.find(eq[0] + " - " + eq[1])
                    print("      no saco la hora de:", cuerpo[max(0, k):max(0, k) + 160])
                print("  ", t, "| cuotas de jugador:", len(jug), "| inicio:",
                      datetime.fromtimestamp(ini, MAD).strftime("%d/%m %H:%M") if ini else None)
                if not ini or not jug:
                    continue
                if ini - time.time() > HORAS * 3600:
                    lejos += 1
                    if lejos >= 2:
                        break   # los siguientes de esta competicion son aun mas lejanos
                    continue
                partidos.append({"inicio": ini, "c1": eq[0], "c2": eq[1], "equipo": [], "total": [],
                                 "jugador": [[k[0], k[1], k[2], c] for k, c in sorted(jug.items())]})
        br.close()
    if partidos:
        json.dump({"ts": time.time(), "partidos": partidos}, open(ARCH, "w", encoding="utf-8"), ensure_ascii=False)
    print("betfair: partidos con cuotas:", len(partidos),
          "| cuotas de jugador:", sum(len(x["jugador"]) for x in partidos))
    print("betfair: tipos de mercado no usados:", sorted(AVISOS["tipos"])[:10])
    if AVISOS["sin_nombre"]:
        print("betfair: AVISO cuotas sin nombre de jugador:", AVISOS["sin_nombre"], "| muestra de corredor:", AVISOS["muestra"])
    if partidos:
        print("betfair: ejemplo:", partidos[0]["jugador"][:4])
    print("betfair: datos gastados aprox %.1f MB | %.0f s" % (BYTES[0] / 1048576.0, time.time() - T0))


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("betfair: fallo controlado:", repr(ex)[:200])
