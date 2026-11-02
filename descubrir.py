import re
import time
import urllib.request

import socketio

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"
SRV = "https://sports-eu-west-3.winamax.es"
PATH = "uof-sports-server/socket.io"
WEB = "https://www.winamax.es/apuestas-deportivas"
H = {"User-Agent": UA, "Origin": "https://www.winamax.es", "Referer": WEB}


def get(url):
    req = urllib.request.Request(url, headers=H)
    r = urllib.request.urlopen(req, timeout=60)
    return r.read().decode("utf-8", "ignore")


def ctx(js, pat, n, w=300):
    c = 0
    for m in re.finditer(pat, js):
        a = max(0, m.start() - w)
        print("  ...", js[a:m.end() + w].replace("\n", " "))
        print("")
        c += 1
        if c >= n:
            break
    print("  total:", len(re.findall(pat, js)))


print("A) CONEXION")
sio = socketio.Client(logger=False, engineio_logger=False)


@sio.on("*")
def todo(ev, *args):
    print("  EVENTO", ev, str(args)[:400])


@sio.event
def connect():
    print("  conectado")


@sio.event
def connect_error(d):
    print("  error de conexion", str(d)[:200])


try:
    sio.connect(SRV, socketio_path=PATH, transports=["websocket"],
                headers=H, wait_timeout=20)
    time.sleep(8)
    sio.disconnect()
except Exception as e:
    print("  fallo", repr(e)[:250])

print("")
print("B) CODIGO DE LA WEB")
page = get(WEB)
m = re.search(r'src="([^"]*static/js/main\.[^"]+\.js)"', page)
js = get(m.group(1))
print("  tamano", len(js))

print("")
print("RUTAS EN TEXTO")
rutas = sorted(set(re.findall(r'route:"([^"]{1,50})"', js)))
print(rutas[:80])

print("")
print("DEFINICION DE RUTAS")
ctx(js, r'HISTORY["\']?\s*[:=]\s*["\']history["\']', 2, 700)

print("")
print("PETICIONES (requestId)")
ctx(js, r"requestId", 4, 260)

print("")
print("RESPUESTAS DEL SERVIDOR")
ctx(js, r'\.on\("m"', 3, 260)
ctx(js, r'on\("meta"', 2, 260)
