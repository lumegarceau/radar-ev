import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

MAD = ZoneInfo("Europe/Madrid")
MESES = {"ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
         "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12}
TIT_JUG = {
    "Tiros a Puerta Totales": "sot",
    "Tiros Totales": "shots",
    "Faltas Cometidas Totales": "fouls",
    "Faltas Recibidas Totales": "drawn",
    "Tackles (Entradas) Totales": "tk",
}
RE_ODD = re.compile(r"^\d+(?:\.\d+)?$")
RE_HEAD = re.compile(r"^\d+$")


def medio(ln):
    return abs(ln % 1 - 0.5) < 0.001


def inicio_de(texto, ahora=None):
    """Marca de tiempo de un texto tipo '12 nov, 20:45'."""
    m = re.search(r"(\d{1,2}) ([a-z]{3})\w*,? (\d{2}):(\d{2})", texto.lower())
    if not m or m.group(2) not in MESES:
        return None
    ahora = ahora or datetime.now(MAD)
    mes = MESES[m.group(2)]
    anyo = ahora.year
    if mes < ahora.month - 6:
        anyo += 1
    try:
        t = datetime(anyo, mes, int(m.group(1)), int(m.group(3)),
                     int(m.group(4)), tzinfo=MAD)
    except ValueError:
        return None
    return t.timestamp()


def equipos_de_fila(texto):
    """Dos nombres de equipo de una fila de la lista de partidos.
    texto con saltos de linea: fecha, equipos y cuotas."""
    lns = [x.strip() for x in texto.split("\n") if x.strip()]
    out = []
    for x in lns:
        if re.search(r"\d{1,2} [a-z]{3}\w*,? \d{2}:\d{2}", x.lower()):
            continue
        if RE_ODD.match(x) or x in ("-", "+", "1", "X", "2"):
            continue
        if len(x) < 3 or x.lower() in ("más", "mas"):
            continue
        out.append(x)
        if len(out) == 2:
            break
    return out if len(out) == 2 else None


def _ou(cuerpo, l1, o1, l2, o2):
    """Devuelve (over, under) si las dos lineas coinciden y son .5"""
    a, b = float(l1), float(l2)
    if abs(a - b) > 1e-6 or not medio(a):
        return None
    return a, float(o1), float(o2)


def parsear_equipo(texto, c1, c2):
    """Mercados de equipo y de totales de la pagina del partido."""
    t = re.sub(r"\s+", " ", texto)
    equipo, total = [], []
    eq = {c1: "home", c2: "away"}
    pref = "(?:(" + "|".join(re.escape(x) for x in (c1, c2)) + ") )?"
    pat = {
        "goals": pref + r"Goles Totales(?: - Más/Menos)?",
        "corners": pref + r"(?:Corners|Córners)(?: - Más/Menos| 2 Opciones)",
    }
    cola = (r"(?: Principal Todo)? Más de Menos de "
            r"(\d+\.\d+) (\d+\.\d+) (\d+\.\d+) (\d+\.\d+)")
    PERIODO = re.compile(r"(?:1\s*[ªa]|2\s*[ªa]|primera|segunda|1st|2nd)\s*(?:parte|mitad|tiempo|half)"
                         r"|(?:parte|mitad|tiempo|half)\s*[12]", re.I)
    for stat, p in pat.items():
        vistos = set()
        for m in re.finditer(p + cola, t):
            lado = eq.get(m.group(1)) if m.group(1) else None
            # los mercados de la 1a/2a parte repiten el titulo: nos quedamos
            # solo con el primero de cada tipo (el del partido completo)
            if (stat, lado) in vistos:
                continue
            if PERIODO.search(t[max(0, m.start() - 60):m.end()]):
                continue
            vistos.add((stat, lado))
            r = _ou(t, m.group(2), m.group(3), m.group(4), m.group(5))
            if not r:
                continue
            ln, co, cu = r
            for s, c in (("over", co), ("under", cu)):
                if lado is None:
                    total.append((stat, ln, c, s))
                else:
                    equipo.append((stat, lado, ln, c, s))
    return equipo, total


def _marcas_equipo(c1, c2):
    return [c1.split(), c2.split()]


def _segmentar(S, N, etiquetas):
    """Parte S (palabras) en N entradas 'nombre + etiqueta de equipo'."""
    nombres, actual, j = [], [], 0
    while j < len(S):
        hit = None
        for e in etiquetas:
            if actual and S[j:j + len(e)] == e:
                hit = e
                break
        if hit:
            nombres.append(" ".join(actual))
            actual = []
            j += len(hit)
            continue
        actual.append(S[j])
        j += 1
    if actual or len(nombres) != N:
        return None
    return nombres


def _inferir(S, N, preferidas):
    """Si las etiquetas esperadas no sirven, busca dos etiquetas (1-3 palabras)
    que expliquen la lista."""
    nombres = _segmentar(S, N, preferidas)
    if nombres:
        return nombres
    cuentas = {}
    for n in (1, 2, 3):
        for i in range(1, len(S) - n + 1):
            g = tuple(S[i:i + n])
            cuentas[g] = cuentas.get(g, 0) + 1
    cand = [g for g, c in cuentas.items() if c >= 2 or N <= 4]
    cand.sort(key=lambda g: (-cuentas[g], -len(g)))
    cand = cand[:60]
    mejor = None
    for a in cand:
        r = _segmentar(S, N, [list(a)])
        if r:
            sc = len(a)
            if mejor is None or sc > mejor[0]:
                mejor = (sc, r)
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            if cuentas[a] + cuentas[b] < N:
                continue
            r = _segmentar(S, N, [list(a), list(b)])
            if r:
                sc = len(a) + len(b)
                if mejor is None or sc > mejor[0]:
                    mejor = (sc, r)
    if mejor:
        return mejor[1]
    return None


def parsear_jugadores(texto, c1, c2):
    """Mercados de jugador de la vista 'Mercado' (columnas por linea).
    Devuelve [(stat, nombre, n, cuota)] y un resumen de secciones."""
    toks = re.sub(r"\s+", " ", texto).split()
    equipos = _marcas_equipo(c1, c2)
    out = []
    resumen = {}
    # posiciones de titulos
    pos = []
    for tit, stat in TIT_JUG.items():
        tt = tit.split()
        for i in range(len(toks) - len(tt) + 1):
            if toks[i:i + len(tt)] == tt:
                if i > 0 and toks[i - 1] in ("a", "con"):
                    continue
                pos.append((i, len(tt), stat, tit))
    pos.sort()
    for k, (i, n, stat, tit) in enumerate(pos):
        j = i + n
        fin = pos[k + 1][0] if k + 1 < len(pos) else len(toks)
        # palabras hasta las cabeceras "1 o +"
        S = []
        while j < len(toks):
            if RE_HEAD.match(toks[j]) and toks[j + 1:j + 3] == ["o", "+"]:
                break
            S.append(toks[j])
            j += 1
            if len(S) > 400:
                break
        if not S or j >= len(toks):
            resumen[tit] = "sin_datos"
            continue
        heads = []
        while j < len(toks) and RE_HEAD.match(toks[j]) \
                and toks[j + 1:j + 3] == ["o", "+"]:
            heads.append(int(toks[j]))
            j += 3
        K = len(heads)
        vals = []
        while j < len(toks):
            x = toks[j]
            if RE_ODD.match(x):
                vals.append(float(x))
            elif x in ("-", "—"):
                vals.append(None)
            else:
                break
            j += 1
        if K == 0 or len(vals) % K:
            resumen[tit] = "columnas_no_cuadran %d/%d" % (len(vals), K)
            continue
        N = len(vals) // K
        nombres = _inferir(S, N, equipos)
        if not nombres:
            resumen[tit] = "no_se_separan_nombres N=%d: %s" % (N, " ".join(S[:14]))
            continue
        for h in range(K):
            for p in range(N):
                v = vals[h * N + p]
                if v:
                    out.append((stat, nombres[p], heads[h], v))
        resumen[tit] = "%d jugadores x %d lineas" % (N, K)
    return out, resumen
