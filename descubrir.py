import re
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://www.valueodds.net"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    r = urllib.request.urlopen(req, timeout=30)
    return r.read().decode("utf-8", "ignore")


home = get(BASE + "/")
links = re.findall(r'href="(/partidos/[^"]+|https://www\.valueodds\.net/partidos/[^"]+)"', home)
print("Partidos en portada:", len(set(links)))
if not links:
    print("Sin partidos hoy")
    raise SystemExit
url = links[0]
if url.startswith("/"):
    url = BASE + url
print("Partido de prueba:", url)
html = get(url)
print("HTML:", len(html), "bytes")

srcs = re.findall(r'<script[^>]+src="([^"]+)"', html)
print("Scripts:", srcs)
textos = {"html": html}
for s in srcs:
    if s.startswith("//"):
        s = "https:" + s
    if s.startswith("/"):
        s = BASE + s
    if "valueodds" in s:
        try:
            textos[s] = get(s)
        except Exception as e:
            print("No se pudo leer", s, str(e)[:60])

rutas = set()
for nombre, t in textos.items():
    for m in re.findall(r'["\'`](/(?:api|v1|data|markets)[^"\'`\s<>]{0,90})', t):
        rutas.add(m)
print("")
print("Rutas internas encontradas:")
for r in sorted(rutas)[:40]:
    print("  ", r)

print("")
for nombre, t in textos.items():
    n = 0
    for m in re.finditer(r'(?i)corner', t):
        a = max(0, m.start() - 70)
        print("[" + nombre[-30:] + "]", t[a:m.end() + 70].replace("\n", " "))
        n += 1
        if n >= 4:
            break
