import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"


class Sin(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


op = urllib.request.build_opener(Sin)


def ver(url):
    h = {"User-Agent": UA, "Accept-Language": "es-ES,es"}
    req = urllib.request.Request(url, headers=h)
    try:
        r = op.open(req, timeout=25)
        cuerpo = r.read(3000).decode("utf-8", "ignore")
        print("  ", r.status, url)
        return r.status, None, cuerpo
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
        print("  ", e.code, url, "->", loc)
        return e.code, loc, ""
    except Exception as e:
        print("  fallo", url, str(e)[:80])
        return 0, None, ""


def cadena(url):
    for i in range(6):
        st, loc, cuerpo = ver(url)
        if loc and st in (301, 302, 303, 307, 308):
            url = urllib.parse.urljoin(url, loc)
            continue
        txt = cuerpo[:200].replace("\n", " ")
        print("   inicio:", txt)
        return


print("1) DESDE DONDE ENTRA GITHUB")
st, loc, c = ver("https://ipinfo.io/json")
print(c[:300].replace("\n", " "))

print("")
print("2) WINAMAX")
cadena("https://www.winamax.es/")
cadena("https://www.winamax.es/apuestas-deportivas")

print("")
print("3) VALUEODDS")
hoy = datetime.now(ZoneInfo("Europe/Madrid")).date()
for i in range(4):
    f = str(hoy + timedelta(days=i))
    u = "https://www.valueodds.net/api/v1/fixtures?date=" + f
    st, loc, c = ver(u)
    h = {"User-Agent": UA}
    try:
        r = urllib.request.urlopen(
            urllib.request.Request(u, headers=h), timeout=25)
        t = r.read().decode("utf-8", "ignore")
        print("  ", f, "partidos:", t.count('"home_team"'))
    except Exception as e:
        print("  ", f, "fallo", str(e)[:60])
