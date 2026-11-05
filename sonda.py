import time
import urllib.request
from datetime import date
from playwright.sync_api import sync_playwright

hoy = str(date.today())
print("== API con reintentos")
for i in range(3):
    for u in ("http://api.clubelo.com/" + hoy, "http://api.clubelo.com/Benfica"):
        try:
            rq = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            t = urllib.request.urlopen(rq, timeout=30).read().decode("utf-8")
            print("OK", u, len(t), t[:150].replace("\n", " | "))
        except Exception as e:
            print("FALLO", i + 1, u, repr(e)[:100])
    time.sleep(10)
print("\n== Web con navegador")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx = br.new_context(user_agent=UA, locale="es-ES")
    for u in ("http://clubelo.com/", "https://clubelo.com/",
              "http://clubelo.com/ENG"):
        pg = ctx.new_page()
        try:
            r = pg.goto(u, timeout=45000, wait_until="domcontentloaded")
            pg.wait_for_timeout(4000)
            t = pg.inner_text("body")
            print("OK", u, "estado:", r.status if r else None,
                  "| titulo:", pg.title(), "| car:", len(t))
            print("   ", t[:300].replace("\n", " | "))
            if "Benfica" in t:
                i = t.find("Benfica")
                print("    Benfica:", t[max(0, i - 20):i + 40].replace("\n", " "))
        except Exception as e:
            print("FALLO", u, repr(e)[:150])
        pg.close()
    br.close()
print("fin")
# fin
