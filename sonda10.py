"""Sonda con proxy español: ¿se leen Luckia, Betsson, Betfair y PokerStars? ¿Cuántos MB gasta cada una?"""
import os
import re
import json
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
RAW = os.environ.get("PROXY_URL", "")
VAL = "".join(RAW.split())
if VAL and "://" not in VAL:
    VAL = "http://" + VAL
if VAL.startswith("http://http"):
    VAL = VAL[len("http://"):]
print("secreto recibido:", "si" if RAW else "NO", "| caracteres:", len(RAW),
      "| espacios o saltos:", len(RAW) - len(VAL.replace("http://", "", 1)) if RAW else 0)
if VAL:
    pre = VAL.split("@")[0]
    print("forma:", "http://" if VAL.startswith("http") else "?",
          "| tiene @:", "@" in VAL, "| usuario:", pre.split("//")[-1].split(":")[0][:40],
          "| host:", VAL.split("@")[-1][:40])
P = urllib.parse.urlparse(VAL)
PROXY = {"server": "%s://%s:%s" % (P.scheme or "http", P.hostname, P.port),
         "username": urllib.parse.unquote(P.username or ""),
         "password": urllib.parse.unquote(P.password or "")}
def ip_publica():
    try:
        h = urllib.request.ProxyHandler({"http": P.geturl(), "https": P.geturl()})
        o = urllib.request.build_opener(h)
        ip = json.loads(o.open("https://api.ipify.org?format=json", timeout=30).read())["ip"]
        g = json.loads(o.open("http://ip-api.com/json/" + ip + "?fields=country,city,isp,hosting", timeout=30).read())
        print("IP del proxy:", ip, g)
    except Exception as e:
        print("no puedo comprobar la IP del proxy:", repr(e)[:150])


SITIOS = [
    ("Betsson", ["https://www.betsson.es/apuestas-deportivas/futbol", "https://www.betsson.es/es/apuestas-deportivas/futbol"]),
    ("Betfair", ["https://www.betfair.es/apuestas/f%C3%BAtbol/s-1"]),
    ("Luckia", ["https://www.luckia.es/apuestas/futbol/", "https://www.luckia.es/apuestas/"]),
]
def ip_publica():
    try:
        h = urllib.request.ProxyHandler({"http": P.geturl(), "https": P.geturl()})
        o = urllib.request.build_opener(h)
        ip = json.loads(o.open("https://api.ipify.org?format=json", timeout=30).read())["ip"]
        g = json.loads(o.open("http://ip-api.com/json/" + ip + "?fields=country,city,isp,hosting", timeout=30).read())
        print("IP del proxy:", ip, g)
    except Exception as e:
        print("no puedo comprobar la IP del proxy:", repr(e)[:150])


PESADO = ("image", "media", "font")
SESION = {"mb": 0.0}
RX_NOM = re.compile(r'"(?:eventName|name|label|title)"\s*:\s*"([^"]{3,45}\s(?:-|v|vs\.?)\s[^"]{3,45})"')
RX_MK = re.compile(r'"(?:label|name|marketName|title|groupLabel)"\s*:\s*"([^"]*(?:[Tt]iro|[Rr]emate|[Ff]alta|[Pp]arada|[Jj]ugador|[Dd]isparo|[Pp]uerta|[Aa]l arco)[^"]*)"')


def nueva(br):
    ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid",
                         viewport={"width": 1366, "height": 2500})
    pg = ctx.new_page()
    pg.route("**/*", lambda r: r.abort() if r.request.resource_type in PESADO else r.continue_())
    pg._json = []
    pg._bytes = [0]

    def fin(rq):
        try:
            sz = rq.sizes()
            pg._bytes[0] += (sz.get("responseBodySize") or 0) + (sz.get("responseHeadersSize") or 0)
        except Exception:
            pass

    def resp(r):
        try:
            if "json" in (r.headers.get("content-type") or "").lower():
                pg._json.append((r.url, r.text(), r.request.method))
        except Exception:
            pass

    pg.on("requestfinished", fin)
    pg.on("response", resp)
    return ctx, pg


def ir(pg, url, espera=15000):
    try:
        r = pg.goto(url, timeout=60000, wait_until="domcontentloaded")
        print("  estado:", r.status if r else None, "| final:", pg.url[:140])
    except Exception as e:
        print("  no carga:", repr(e)[:120])
        return False
    pg.wait_for_timeout(espera)
    return True


def cookies(pg):
    for t in ("Aceptar todas las cookies", "Aceptar todas", "Aceptar", "Entendido"):
        try:
            l = pg.get_by_text(t, exact=False).first
            if l.count():
                l.click(timeout=3000)
                pg.wait_for_timeout(2500)
                print("  cookies aceptadas con:", t)
                return
        except Exception:
            pass


def gasto(pg, et):
    mb = pg._bytes[0] / 1048576.0
    SESION["mb"] += mb
    print("  [%s] gastado %.2f MB | JSON: %d" % (et, mb, len(pg._json)))


def nombres(pg):
    vis = []
    for u, c, m in pg._json:
        for x in RX_NOM.findall(c):
            if x not in vis:
                vis.append(x)
    return vis


def mercados(pg):
    cnt = {}
    for u, c, m in pg._json:
        for x in RX_MK.findall(c):
            cnt[x] = cnt.get(x, 0) + 1
    print("  mercados con tiros/remates/faltas/paradas/jugador/puerta (%d distintos):" % len(cnt))
    for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:40]:
        print("     -", k[:90], "x", v)
    big = sorted(pg._json, key=lambda x: -len(x[1]))[:6]
    for u, c, m in big:
        print("  JSON grande:", m, u[:150], "| tam:", len(c))


def trozo(txt, marca, ant=300, des=900):
    k = txt.find(marca)
    return None if k < 0 else txt[max(0, k - ant):k + des]


def enmascara(t):
    return re.sub(r'("(?:[Tt]oken|sessionToken|sessiontoken)"\\s*:\\s*")[^"]{8,}', r'\\1***', t)


def betsson(br):
    from datetime import datetime, timezone, timedelta
    print("\n===== Betsson partido futuro", flush=True)
    ctx, pg = nueva(br)
    if not ir(pg, "https://www.betsson.es/apuestas-deportivas/futbol"):
        ctx.close()
        return
    cookies(pg)
    pg.wait_for_timeout(8000)
    gasto(pg, "Betsson listado")
    evs = {}

    def busca(x, prof=0):
        if prof > 10:
            return
        if isinstance(x, dict):
            if x.get("slug") and x.get("participants") and x.get("startDate"):
                evs[x["slug"]] = x
                return
            for v in x.values():
                busca(v, prof + 1)
        elif isinstance(x, list):
            for v in x:
                busca(v, prof + 1)
    for u, c, m in pg._json:
        if len(c) < 14000000 and "slug" in c:
            try:
                busca(json.loads(c))
            except Exception:
                pass
    lim = (datetime.now(timezone.utc) + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
    fut = [e for e in evs.values() if e["startDate"][:16] > lim]
    print("  eventos totales:", len(evs), "| futuros:", len(fut), "| fases:", sorted(set(str(e.get("phase")) for e in evs.values())))
    for e in sorted(fut, key=lambda e: e["startDate"])[:8]:
        print("   ", e["startDate"], "|", e.get("label") or [p["label"] for p in e["participants"]], "| mercados:", e.get("marketCount"), "| jugadores:", len(e.get("subParticipants") or []), "|", e["slug"])
    if not fut:
        ctx.close()
        return
    pref = [e for e in fut if any("Espa" in p.get("label", "") for p in e["participants"])]
    e = (pref or sorted(fut, key=lambda e: -(e.get("marketCount") or 0)))[0]
    print("  ELEGIDO:", e["slug"], e["startDate"])
    pg._json.clear()
    pg._bytes[0] = 0
    if not ir(pg, "https://www.betsson.es/apuestas-deportivas/" + e["slug"], 18000):
        ctx.close()
        return
    for t in ("Jugadores", "Tiros", "Especiales de jugador", "Estad. jugador", "Pronósticos de jugador"):
        try:
            l = pg.get_by_text(t, exact=True).first
            if l.count():
                l.click(timeout=2500)
                pg.wait_for_timeout(3500)
                print("  pulsado:", t)
        except Exception:
            pass
    gasto(pg, "Betsson partido")
    pref = {}
    for u, c, m in pg._json:
        for x in re.findall(r'"label"\s*:\s*"([^"|]{3,60}) \| [^"]{3,40}"', c):
            pref[x] = pref.get(x, 0) + 1
    print("  tipos de mercado 'X | jugador' (%d):" % len(pref))
    for k, v in sorted(pref.items(), key=lambda kv: -kv[1])[:30]:
        print("     -", k, "x", v)
    mostrado = 0
    for u, c, m in pg._json:
        for marca in ("Total de tiros al arco |", "Total de faltas |", "Tiros |"):
            k = c.find(marca)
            if k >= 0 and mostrado < 2:
                mostrado += 1
                print(" MERCADO DE JUGADOR:", m, u[:160], "| marca:", marca, "| tam", len(c))
                print("   ", c[max(0, k - 700):k + 1800].replace("\n", " "))
                break
    ctx.close()


def betfair(br):
    print("\n===== Betfair partido", flush=True)
    ctx, pg = nueva(br)
    if not ir(pg, "https://www.betfair.es/apuestas/f%C3%BAtbol/s-1"):
        ctx.close()
        return
    cookies(pg)
    pg.wait_for_timeout(8000)
    malas = re.compile(r"Femenin|\\(W\\)|Serie|Cup|Liga|League|Games|UEFA|Plataforma|Platform|Brasil", re.I)
    cands = []
    for n in nombres(pg):
        izq, _, der = n.partition(" - ")
        if der and not malas.search(n) and izq not in cands:
            cands.append(izq)
    print("  candidatos:", cands[:8])
    for izq in cands[:5]:
        pg._json.clear()
        pg._bytes[0] = 0
        try:
            pg.get_by_text(izq, exact=True).first.click(timeout=4000)
        except Exception as e:
            print("  no pude pulsar", izq, repr(e)[:70])
            continue
        pg.wait_for_timeout(12000)
        print("  pulsado:", izq, "| url:", pg.url[:150])
        if "/s-1" in pg.url and pg.url.rstrip("/").endswith("s-1"):
            continue
        for t in ("Jugadores", "Remates", "Tiros", "Especiales", "Más mercados"):
            try:
                l = pg.get_by_text(t, exact=True).first
                if l.count():
                    l.click(timeout=2500)
                    pg.wait_for_timeout(3000)
            except Exception:
                pass
        gasto(pg, "Betfair partido")
        mercados(pg)
        print("  texto:", " ".join(pg.inner_text("body").split())[:600])
        break
    ctx.close()


if not P.hostname:
    print("Falta el secreto PROXY_URL")
    raise SystemExit(1)
ip_publica()
with sync_playwright() as pw:
    br = pw.chromium.launch(proxy=PROXY)
    for f in (betsson,):
        try:
            f(br)
        except StopIteration:
            pass
        except Exception as e:
            print(f.__name__, "falla", repr(e)[:150])
    br.close()
print("\nTOTAL GASTADO: %.2f MB" % SESION["mb"])
