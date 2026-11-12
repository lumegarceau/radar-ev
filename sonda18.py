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



PESADO = ("image", "media", "font")
MK = re.compile(r"tiro|remate|falta|parada|jugador|puerta|arco", re.I)
STEALTH = ("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
           "Object.defineProperty(navigator,'languages',{get:()=>['es-ES','es']});window.chrome={runtime:{}};")



def caminar(x, f):
    if isinstance(x, dict):
        f(x)
        for v in x.values():
            caminar(v, f)
    elif isinstance(x, list):
        for v in x:
            caminar(v, f)


def main():
    ip_publica()
    with sync_playwright() as p:
        br = p.chromium.launch(proxy=PROXY)
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid", viewport={"width": 1366, "height": 3000})
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
        pg.on("response", resp)
        pg.on("request", req)
        pg.goto("https://www.betfair.es/apuestas/f%C3%BAtbol/liga-a-de-naciones-de-la-uefa/turqu%C3%ADa-b%C3%A9lgica/e-36191447", timeout=60000, wait_until="domcontentloaded")
        for i in range(8):
            pg.wait_for_timeout(4000)
            if "momento" not in pg.title().lower():
                break
        pg.wait_for_timeout(10000)
        print("PARTIDO:", pg.title(), "| respuestas:", len(got), "| peticiones Card#:", len(reqs))
        if not reqs:
            return
        url, hd, post0 = reqs[0]
        print("URL peticion:", url[:200])
        print("cabeceras:", sorted(hd.keys()))
        print("documentId:", json.loads(post0).get("documentId"))
        # grupos y tarjetas
        grupos = []
        def f(d):
            if d.get("__typename") == "PebbleCardGroup":
                t = ((d.get("pebbleCardGroupTitle") or {}).get("translated")) or "?"
                for e in ((d.get("partials") or {}).get("edges") or []):
                    u = (e.get("node") or {}).get("urn")
                    if u:
                        grupos.append((t, e.get("name"), u))
        for t in got:
            try:
                caminar(json.loads(t), f)
            except Exception:
                pass
        vistos, uniq = set(), []
        for g in grupos:
            if g[2] not in vistos:
                vistos.add(g[2]); uniq.append(g)
        print("\nmercados (grupo | parte | urn): %d tarjetas" % len(uniq))
        titulos = []
        for t, n, u in uniq:
            if t not in titulos:
                titulos.append(t)
        print("TITULOS:", titulos)
        sel = [g for g in uniq if MK.search(g[0])][:14]
        print("\ntarjetas a pedir:", len(sel))
        for g in sel:
            print("   ", g[0], "|", g[1], "|", g[2][-40:])
        if not sel:
            return
        base = json.loads(post0)
        hdr = {k: v for k, v in hd.items() if not k.startswith(":") and k not in ("content-length", "host", "cookie", "origin", "referer", "user-agent", "accept-encoding", "connection")}
        out = []
        for i in range(0, len(sel), 5):
            lote = [g[2] for g in sel[i:i + 5]]
            b = dict(base); v = dict(base["variables"]); v["urn"] = lote; b["variables"] = v
            r = pg.evaluate("""async ([u,h,b])=>{const r=await fetch(u,{method:'POST',headers:h,body:b,credentials:'include'});return {s:r.status,t:await r.text()}}""", [url, hdr, json.dumps(b)])
            print("\nlote", i // 5, "estado", r["s"], "bytes", len(r["t"]))
            out.append(r["t"])
        txt = out[0] if out else ""
        print("\nMUESTRA RESPUESTA 1:")
        print(txt[:3500])
        k = txt.find("price")
        if k < 0:
            k = txt.lower().find("odds")
        print("\nEN TORNO A PRECIO:", txt[max(0, k - 600):k + 900] if k >= 0 else "(no hay price/odds)")
        ctx.close()
        br.close()


main()
