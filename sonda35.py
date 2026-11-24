"""Sonda: que dominios de Kirolbet/Juegging dejan pasar al navegador, con y sin proxy."""
import os
import urllib.parse
from playwright.sync_api import sync_playwright

URLS = ["https://www.kirolbet.es/", "https://apuestas.kirolbet.es/",
        "https://www.juegging.es/", "https://apuestas.juegging.es/",
        "https://sports.kirolbet.es/"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


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


with sync_playwright() as pw:
    for usa in (True, False):
        pr = proxy() if usa else None
        if usa and not pr:
            continue
        br = pw.chromium.launch(proxy=pr) if pr else pw.chromium.launch()
        ctx = br.new_context(user_agent=UA, locale="es-ES", timezone_id="Europe/Madrid")
        for u in URLS:
            pg = ctx.new_page()
            try:
                r = pg.goto(u, timeout=45000, wait_until="domcontentloaded")
                pg.wait_for_timeout(6000)
                t = " ".join(pg.inner_text("body").split())
                print("proxy" if usa else "sin proxy", "|", u, "| http", r.status if r else None,
                      "| final", pg.url[:70], "| titulo:", pg.title()[:50], "| chars", len(t), "|", t[:90])
            except Exception as e:
                print("proxy" if usa else "sin proxy", "|", u, "| falla:", repr(e)[:90])
            pg.close()
        br.close()
