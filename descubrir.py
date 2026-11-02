import http.cookiejar
import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
op.addheaders = [
    ("User-Agent", UA),
    ("Accept-Language", "es-ES,es;q=0.9"),
    ("Accept", "text/html,application/xhtml+xml"),
]
SIG = ["PRELOADED_STATE", "__INITIAL_STATE__", "__NEXT_DATA__",
       "socket.io", "wss://", "uof-sports", "sports-eu"]


def get(url):
    try:
        r = op.open(url, timeout=30)
        t = r.read().decode("utf-8", "ignore")
        return r.status, r.geturl(), t
    except Exception as e:
        print("fallo", url, str(e)[:100])
        return 0, url, ""


def senales(t):
    for s in SIG:
        i = t.find(s)
        if i >= 0:
            a = max(0, i - 80)
            print("  senal", s, ":", t[a:i + 160].replace("\n", " "))


def revisar(url):
    st, u, t = get(url)
    print("")
    print(st, u, len(t))
    senales(t)
    srcs = re.findall(r'<script[^>]+src="([^"]+)"', t)
    print("  scripts:", srcs[:12])
    n = len(re.findall(r"(?i)c[oó]rner", t))
    print("  menciones a corners:", n)
    return t


t = revisar("https://www.winamax.es/apuestas-deportivas")
links = sorted(set(re.findall(r'href="(/apuestas-deportivas/[^"#?]+)"', t)))
print("Enlaces:", len(links))
for x in links[:30]:
    print(" ", x)

t2 = revisar("https://www.winamax.es/apuestas-deportivas/sports/1")
l2 = sorted(set(re.findall(r'href="(/apuestas-deportivas/[^"#?]+)"', t2)))
print("Enlaces futbol:", len(l2))
for x in l2[:30]:
    print(" ", x)
m = [x for x in l2 + links if "match" in x]
print("Enlaces de partido:", len(m))
if m:
    revisar("https://www.winamax.es" + m[0])
