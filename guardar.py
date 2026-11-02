import json
from datetime import datetime
from zoneinfo import ZoneInfo

MAD = ZoneInfo("Europe/Madrid")
FH = "historial.json"
FR = "radar-data.json"


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
    print("sin cambios desde la ultima vez")
    raise SystemExit
ahora = datetime.now(MAD)
ts = ahora.isoformat(timespec="minutes")
nuevas = 0
act = 0
for c in radar["days"][-1]["candidatos"]:
    ini = inicio_de(c.get("hora", ""), ahora)
    if ini is None or ahora >= ini:
        continue
    cu, b = mejor(c)
    obs = {"c": cu, "b": b, "t": ts}
    k = str(c["fixture"]) + "|" + c["suceso"]
    r = sel.get(k)
    if r is None:
        sel[k] = {
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
        nuevas += 1
        continue
    if r["estado"] != "pendiente":
        continue
    r["prob"] = c["prob"]
    r["ultima"] = obs
    if cu > r["max"]["c"]:
        r["max"] = obs
    act += 1
meta["updated_at"] = radar.get("updated_at")
json.dump(H, open(FH, "w"), ensure_ascii=False)
print("selecciones nuevas:", nuevas, "| actualizadas:", act)
print("total en historial:", len(sel))
