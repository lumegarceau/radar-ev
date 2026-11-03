import json
from datetime import datetime
from zoneinfo import ZoneInfo

MAD = ZoneInfo("Europe/Madrid")
FH = "historial.json"
FR = "radar-data.json"
CAMPOS = ["tid", "hid", "aid", "lid", "pid", "num", "pos", "serie",
          "media", "minmed", "por90", "tit", "sentido", "duda"]


def cargar(f, vacio):
    try:
        return json.load(open(f))
    except Exception:
        return vacio


def inicio_de(hora, ahora):
    try:
        d, h = hora.split(" ")
        dd, mm = d.split("/")
        hh, mi = h.split(":")
        a = ahora.year
        t = datetime(a, int(mm), int(dd), int(hh), int(mi), tzinfo=MAD)
        if (ahora - t).days > 200:
            t = t.replace(year=a + 1)
        return t
    except Exception:
        return None


def mejor(c):
    q = max(c["cuotas"], key=lambda o: o["c"])
    return q["c"], q["b"]


radar = cargar(FR, None)
if not radar or not radar.get("days"):
    print("sin radar-data.json")
    raise SystemExit
H = cargar(FH, {"meta": {}, "sel": {}})
meta = H.setdefault("meta", {})
sel = H.setdefault("sel", {})
if meta.get("updated_at") == radar.get("updated_at"):
    if meta.get("v") == 7:
        print("sin cambios desde la ultima vez")
        raise SystemExit
props_ok = bool(radar.get("props_ok"))
ahora = datetime.now(MAD)
ts = ahora.isoformat(timespec="minutes")
nuevas = 0
act = 0
vistas = set()
for c in radar["days"][-1]["candidatos"]:
    ini = inicio_de(c.get("hora", ""), ahora)
    if ini is None or ahora >= ini:
        continue
    cu, b = mejor(c)
    obs = {"c": cu, "b": b, "t": ts}
    k = str(c["fixture"]) + "|" + c["suceso"]
    vistas.add(k)
    extra = {
        "hora": c.get("hora"),
        "l20": c.get("l20"),
        "l10": c.get("l10"),
        "cond": c.get("cond"),
        "rival": c.get("rival"),
        "cuotas": c["cuotas"],
        "dia": ini.strftime("%Y-%m-%d"),
        "aus": 0,
        "vigente": True,
    }
    for campo in CAMPOS:
        extra[campo] = c.get(campo)
    r = sel.get(k)
    if r is None:
        r = {
            "fixture": c["fixture"],
            "pais": c["pais"],
            "liga": c["liga"],
            "local": c["local"],
            "visitante": c["visitante"],
            "inicio": ini.isoformat(timespec="minutes"),
            "suceso": c["suceso"],
            "mercado": c.get("mercado"),
            "linea": c.get("linea"),
            "tipo": c.get("tipo", "equipo"),
            "equipo": c.get("equipo"),
            "condTxt": c.get("condTxt"),
            "prob": c["prob"],
            "prob0": c["prob"],
            "primera": obs,
            "ultima": obs,
            "max": obs,
            "estado": "pendiente",
        }
        r.update(extra)
        sel[k] = r
        nuevas += 1
        continue
    if r["estado"] != "pendiente":
        continue
    r.update(extra)
    r["prob"] = c["prob"]
    r["ultima"] = obs
    if cu > r["max"]["c"]:
        r["max"] = obs
    act += 1
ocultas = 0
for k, r in sel.items():
    r.setdefault("dia", str(r["inicio"])[:10])
    if k in vistas or r["estado"] != "pendiente":
        continue
    if ahora >= datetime.fromisoformat(r["inicio"]):
        continue
    if r.get("tipo") == "jugador" and not props_ok:
        continue
    r["aus"] = r.get("aus", 0) + 1
    r["vigente"] = r["aus"] < 2
    if not r["vigente"]:
        ocultas += 1
meta["updated_at"] = radar.get("updated_at")
meta["v"] = 7
json.dump(H, open(FH, "w"), ensure_ascii=False)
print("pasada de props completa:", props_ok)
print("selecciones nuevas:", nuevas, "| actualizadas:", act)
print("ocultas por dejar de cumplir:", ocultas)
print("total en historial:", len(sel))
