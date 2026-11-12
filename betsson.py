"""Lee las cuotas de jugador de Betsson (remates, remates a puerta, faltas) con proxy español.
Sale betsson.json con el mismo formato que juegging.json."""
import json
import os
import re
import sys
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

from playwright.sync_api import sync_playwright

ARCH = "betsson.json"
LISTADO = "https://www.betsson.es/apuestas-deportivas/futbol"
API = "https://www.betsson.es/api/sb/v1/widgets/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
HORAS = 40            # solo partidos que empiezan en las proximas horas
MAX_EVENTOS = 40
LIMITE_S = 25 * 60
# etiqueta exacta del mercado de jugador -> estadistica del radar
STAT = {"Total de tiros al arco": "sot", "Total de tiros": "shots",
        "Faltas cometidas": "fouls"}
PROHIBIDAS = ("cookie", "user-agent", "referer", "host", "content-length",
              "accept-encoding", "connection", "origin")
RE_MAS = re.compile(r"^m[aá]s de (\d+(?:\.\d+)?)$", re.I)
T0 = time.time()
BYTES = [0]


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


def epoch(iso):
    return datetime.strptime(iso[:16], "%Y-%m-%dT%H:%M").replace(
        tzinfo=timezone.utc).timestamp()


def eventos_de(json_txt, acum):
    """Recorre un JSON y guarda los eventos (con slug, participantes y fecha)."""
    try:
        j = json.loads(json_txt)
    except Exception:
        return

    def busca(x, prof=0):
        if prof > 10:
            return
        if isinstance(x, dict):
            if x.get("slug") and x.get("participants") and x.get("startDate"):
                acum[x["slug"]] = x
                return
            for v in x.values():
                busca(v, prof + 1)
        elif isinstance(x, list):
            for v in x:
                busca(v, prof + 1)
    busca(j)


def id_evento(e):
    i = str(e.get("id") or "")
    if i.startswith("f-"):
        return i
    m = re.search(r"(f-[A-Za-z0-9_\-]+)$", str(e.get("globalId") or ""))
    return m.group(1) if m else None


def grupos_jugador(txt):
    """De la respuesta event/v2 saca {groupableId: etiqueta} de los grupos que queremos."""
    out = {}
    try:
        j = json.loads(txt)
    except Exception:
        return out

    def busca(x, prof=0):
        if prof > 12:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, dict) and v.get("label") in STAT and \
                        ("marketTemplateIds" in v or "groupableId" in v):
                    out[v.get("groupableId") or k] = v["label"]
                else:
                    busca(v, prof + 1)
        elif isinstance(x, list):
            for v in x:
                busca(v, prof + 1)
    busca(j)
    return out


def selecciones(txt):
    """De una respuesta accordion saca [(stat, jugador, n, cuota)]."""
    try:
        j = json.loads(txt)
    except Exception:
        return [], set()
    mercados = {}
    sels = []
    otros = set()

    def busca(x, prof=0):
        if prof > 12:
            return
        if isinstance(x, dict):
            if str(x.get("id", "")).startswith("m-") and x.get("label"):
                mercados[x["id"]] = x["label"]
            if x.get("marketId") and "odds" in x:
                sels.append(x)
            for v in x.values():
                busca(v, prof + 1)
        elif isinstance(x, list):
            for v in x:
                busca(v, prof + 1)
    busca(j)
    out = []
    for s in sels:
        lab = mercados.get(s["marketId"], "")
        if " | " not in lab or s.get("status") != "Open":
            continue
        tipo, jug = lab.split(" | ", 1)
        stat = STAT.get(tipo.strip())
        if not stat:
            otros.add(tipo.strip())
            continue
        m = RE_MAS.match(str(s.get("alternateLabel") or s.get("participantLabel") or "").strip())
        if not m:
            continue
        n = int(float(m.group(1))) + 1
        try:
            c = float(s["odds"])
        except Exception:
            continue
        if c > 1.0:
            out.append((stat, jug.strip(), n, c))
    return out, otros


def main():
    px = proxy()
    if not px:
        print("betsson: falta PROXY_URL; no se lee nada")
        return
    ahora = datetime.now(timezone.utc)
    lim = (ahora + timedelta(hours=HORAS)).strftime("%Y-%m-%dT%H:%M")
    ini = (ahora + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M")
    evs = {}
    hdr = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(proxy=px)
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                             viewport={"width": 1366, "height": 2500})
        pg = ctx.new_page()
        pg.route("**/*", lambda r: r.abort() if r.request.resource_type in ("image", "media", "font") else r.continue_())

        def peticion(r):
            if "/api/sb/v1/widgets/" in r.url and "sessiontoken" in r.headers:
                hdr.clear()
                hdr.update(r.headers)

        def fin(rq):
            try:
                s = rq.sizes()
                BYTES[0] += (s.get("responseBodySize") or 0) + (s.get("responseHeadersSize") or 0)
            except Exception:
                pass

        def resp(r):
            try:
                if "json" in (r.headers.get("content-type") or "").lower() and "/widgets/" in r.url:
                    t = r.text()
                    if "slug" in t:
                        eventos_de(t, evs)
            except Exception:
                pass

        pg.on("request", peticion)
        pg.on("requestfinished", fin)
        pg.on("response", resp)
        pg.goto(LISTADO, timeout=60000, wait_until="domcontentloaded")
        for t in ("Aceptar todas las cookies",):
            try:
                l = pg.get_by_text(t, exact=False).first
                if l.count():
                    l.click(timeout=3000)
            except Exception:
                pass
        pg.wait_for_timeout(15000)
        h = {k: v for k, v in hdr.items()
             if not k.startswith(":") and not k.startswith("sec-") and k not in PROHIBIDAS}
        print("betsson: eventos en el listado:", len(evs), "| cabeceras capturadas:", len(h),
              "| sessiontoken:", "si" if "sessiontoken" in h else "NO")
        if not h or "sessiontoken" not in h:
            print("betsson: sin sesion, se termina")
            br.close()
            return

        def pedir(url):
            return pg.evaluate("""async ([u,h])=>{try{const r=await fetch(u,{headers:h,credentials:'include'});
                return [r.status, await r.text()]}catch(e){return [0,String(e)]}}""", [url, h])

        sel = []
        for e in sorted(evs.values(), key=lambda e: e["startDate"]):
            f = e["startDate"][:16]
            if f <= ini or f > lim or len(e.get("subParticipants") or []) < 10:
                continue
            if e.get("phase") == "Live":
                continue
            sel.append(e)
        sel = sel[:MAX_EVENTOS]
        print("betsson: partidos a leer:", len(sel))
        partidos = []
        otros = set()
        for e in sel:
            if time.time() - T0 > LIMITE_S:
                print("betsson: limite de tiempo, se corta")
                break
            eid = id_evento(e)
            ps = sorted(e["participants"], key=lambda p: p.get("side", 0))
            if not eid or len(ps) < 2:
                continue
            st, txt = pedir(API + "event/v2?eventId=%s&subTabs=133" % eid)
            if st != 200:
                print("  ", e["slug"][-40:], "event/v2 estado", st, txt[:80])
                continue
            gr = grupos_jugador(txt)
            jug = {}
            for gid, lab in gr.items():
                st2, t2 = pedir(API + "accordion/v1?eventId=%s&groupableId=%s" % (eid, gid))
                if st2 != 200:
                    print("   accordion", gid, "estado", st2)
                    continue
                res, ot = selecciones(t2)
                otros |= ot
                for stat, nom, n, c in res:
                    k = (stat, nom, n)
                    if c > jug.get(k, 0):
                        jug[k] = c
            print("  ", ps[0]["label"], "-", ps[1]["label"], "| grupos:", len(gr), "| cuotas de jugador:", len(jug))
            if jug:
                partidos.append({"inicio": epoch(e["startDate"]), "c1": ps[0]["label"],
                                 "c2": ps[1]["label"], "equipo": [], "total": [],
                                 "jugador": [[k[0], k[1], k[2], c] for k, c in sorted(jug.items())]})
        br.close()
    if partidos:
        json.dump({"ts": time.time(), "partidos": partidos}, open(ARCH, "w", encoding="utf-8"),
                  ensure_ascii=False)
    print("betsson: partidos con cuotas:", len(partidos),
          "| cuotas de jugador:", sum(len(p["jugador"]) for p in partidos),
          "| tipos de mercado de jugador no usados:", sorted(otros)[:12])
    print("betsson: datos gastados %.1f MB | %.0f s" % (BYTES[0] / 1048576.0, time.time() - T0))


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print("betsson: fallo controlado:", repr(ex)[:200])
