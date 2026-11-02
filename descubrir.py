import re
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
SRV = "https://sports-eu-west-3.winamax.es"
PATH = "/uof-sports-server/socket.io/"
H = {
    "User-Agent": UA,
    "Origin": "https://www.winamax.es",
    "Referer": "https://www.winamax.es/apuestas-deportivas",
}


def get(url):
    req = urllib.request.Request(url, headers=H)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "ignore")
    except Exception as e:
        return 0, str(e)[:100]


def ctx(t, pat, n, w=90):
    c = 0
    for m in re.finditer(pat, t):
        a = max(0, m.start() - w)
        print("  ...", t[a:m.end() + w].replace("\n", " "))
        c += 1
        if c >= n:
            break
    print("  total:", len(re.findall(pat, t)))


print("1) HANDSHAKE")
for eio in ("3", "4"):
    u = SRV + PATH + "?EIO=" + eio + "&transport=polling"
    st, t = get(u)
    print(" EIO", eio, st, t[:250].replace("\n", " "))

print("")
print("2) CODIGO DE LA PAGINA")
st, page = get("https://www.winamax.es/apuestas-deportivas")
m = re.search(r'src="([^"]*static/js/main\.[^"]+\.js)"', page)
if not m:
    print("sin main.js")
    raise SystemExit
url = m.group(1)
print(url)
st, js = get(url)
print("estado", st, "tamano", len(js))
for pat in [r"\.emit\(", r"transports", r"[\"']route[\"']", r"(?i)corner"]:
    print("")
    print("PATRON", pat)
    ctx(js, pat, 6)

print("")
print("3) OTROS TROZOS DE CODIGO")
chunks = sorted(set(re.findall(r'static/js/[^"\']+\.js', js)))
print("trozos:", len(chunks), chunks[:15])
