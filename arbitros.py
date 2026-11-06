import json
import os
import unicodedata
from datetime import datetime
from rcommon import api, gasto
import rmodelo

TEMP = 2026
RECIENTES = 10
NUEVAS_MAX = 150
UNID = {"fouls": "faltas", "cards": "tarjetas", "drawn": "faltas"}
OK = ("FT", "AET", "PEN")


def norm(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if c.isalnum() or c == " ")
    return " ".join(s.split())


def nombre(ref):
    return str(ref or "").split(",")[0].strip()


def num(v):
    return str(round(v, 1)).replace(".", ",")


def lin(v):
    return str(v).replace(".", ",")


def fnum(v):
    return float(v) if v is not None else None


def valores(fid, fecha, nuevas):
    f = "cache/s" + str(fid) + ".json"
    if not os.path.exists(f):
        if nuevas[0] >= NUEVAS_MAX:
            return None
        nuevas[0] += 1
    return rmodelo.stats(fid, fecha[:10] < rmodelo.CORTE)


def corto(ref):
    t = norm(nombre(ref)).split()
    if not t:
        return ""
    return t[0][:1] + " " + t[-1]


def partidos_arbitro(lista, ref, antes_de, nuevas, info=None):
    clave = norm(nombre(ref))
    mios = []
    jugados = [x for x in lista if x["fixture"]["status"]["short"] in OK
               and x["fixture"].get("referee")]
    for x in jugados:
        if norm(nombre(x["fixture"].get("referee"))) == clave:
            mios.append(x)
    if not mios:
        ck = corto(ref)
        for x in jugados:
            if corto(x["fixture"].get("referee")) == ck:
                mios.append(x)
    if info is not None:
        info["jugados_con_arbitro"] = len(jugados)
        info["suyos"] = len(mios)
    mios.sort(key=lambda x: x["fixture"]["date"], reverse=True)
    out = []
    for x in mios:
        if len(out) >= RECIENTES:
            break
        d = valores(x["fixture"]["id"], x["fixture"]["date"], nuevas)
        if not d:
            continue
        h = d.get(str(x["teams"]["home"]["id"]))
        a = d.get(str(x["teams"]["away"]["id"]))
        if not h or not a:
            continue
        out.append({"h": h, "a": a})
    return out


def cuenta(vals, linea, sentido):
    if sentido == "under":
        return sum(1 for v in vals if v < linea)
    return sum(1 for v in vals if v > linea)


def lineas_de(c, ps, nom, liga):
    st = c["mercado"]
    k = "cards" if st == "cards" else "fouls"
    u = UNID[st]
    sent = c.get("sentido") or "over"
    tot = [p["h"][k] + p["a"][k] for p in ps if k in p["h"] and k in p["a"]]
    if not tot:
        return None
    n = len(tot)
    pre = nom + " en " + liga + " (" + str(n) + " partidos)"
    out = []
    if c["tipo"] == "total":
        out.append("Media del partido con " + pre + ": " + num(sum(tot) / n)
                   + " " + u + ".")
        h = cuenta(tot, c["linea"], sent)
        out.append(str(h) + "/" + str(n) + " con "
                   + ("menos" if sent == "under" else "más") + " de "
                   + lin(c["linea"]) + " " + u + ".")
    elif c["tipo"] == "equipo":
        lado = "h" if c.get("condTxt") == "local" else "a"
        v = [p[lado][k] for p in ps if k in p[lado]]
        if not v:
            return None
        n2 = len(v)
        quien = "locales" if lado == "h" else "visitantes"
        uno = "local" if lado == "h" else "visitante"
        out.append("Con " + pre + ", los " + quien + " promedian "
                   + num(sum(v) / n2) + " " + u + " y el partido "
                   + num(sum(tot) / n) + " en total.")
        h = cuenta(v, c["linea"], sent)
        out.append(str(h) + "/" + str(n2) + " con "
                   + ("menos" if sent == "under" else "más") + " de "
                   + lin(c["linea"]) + " para el equipo " + uno + ".")
    else:
        out.append("Media del partido con " + pre + ": " + num(sum(tot) / n)
                   + " faltas.")
        kc = [p["h"]["cards"] + p["a"]["cards"] for p in ps
              if "cards" in p["h"] and "cards" in p["a"]]
        if kc:
            out.append("Tarjetas: " + num(sum(kc) / len(kc)) + " por partido.")
    if n < 5:
        out.append("Muestra pequeña: toma el dato solo como referencia.")
    return out


def main():
    fn = "radar-data.json"
    data = json.load(open(fn))
    cs = data["days"][-1]["candidatos"]
    for c in cs:
        c.pop("arb", None)
    obj = [c for c in cs if c.get("mercado") in UNID]
    ligas = sorted(set(c["lid"] for c in obj if c.get("lid") is not None))
    listas = {}
    for lid in ligas:
        listas[lid] = api("/fixtures", league=lid, season=TEMP) or []
        print("arbitros: liga", lid, "->", len(listas[lid]), "partidos")
    nuevas = [0]
    ref_de = {}
    for lid, lst in listas.items():
        for x in lst:
            ref_de[x["fixture"]["id"]] = x["fixture"].get("referee")
    cache = {}
    sin_datos = []
    con = 0
    sin_ref = 0
    for c in obj:
        ref = ref_de.get(c["fixture"])
        if not ref:
            sin_ref += 1
            continue
        key = (c["lid"], norm(nombre(ref)))
        if key not in cache:
            inf = {}
            cache[key] = partidos_arbitro(listas[c["lid"]], ref, None,
                                          nuevas, inf)
            if not cache[key]:
                sin_datos.append((c.get("liga"), nombre(ref),
                                  inf.get("jugados_con_arbitro"),
                                  inf.get("suyos")))
        ps = cache[key]
        if not ps:
            continue
        ln = lineas_de(c, ps, nombre(ref), c.get("liga") or "la competición")
        if ln:
            c["arb"] = {"nom": nombre(ref), "n": len(ps), "l": ln}
            con += 1
    json.dump(data, open(fn, "w"), ensure_ascii=False)
    print("arbitros: candidatos de faltas/tarjetas:", len(obj),
          "| con datos de arbitro:", con, "| sin arbitro asignado:", sin_ref)
    por = {}
    for c in obj:
        k = c.get("liga")
        v = por.setdefault(k, [0, 0])
        v[0] += 1
        if c.get("arb"):
            v[1] += 1
    print("arbitros: por liga (candidatos, con datos):", por)
    print("arbitros: arbitros sin datos (liga, nombre, partidos jugados "
          "con arbitro en la liga, partidos suyos):", sin_datos[:15])
    print("arbitros: arbitros distintos:", len(cache),
          "| estadisticas nuevas pedidas:", nuevas[0],
          "| peticiones API:", gasto[0])


try:
    main()
except Exception as e:
    print("arbitros: fallo", repr(e)[:200])
# fin
