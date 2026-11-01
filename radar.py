import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from rcommon import api, gasto
from rmodelo import historial, analizar

MAD = ZoneInfo("Europe/Madrid")
TEMP = 2026
DIAS = 2
LIGAS = {
    140: ("España", "LaLiga"),
    39: ("Inglaterra", "Premier League"),
    135: ("Italia", "Serie A"),
}
CASAS = set([
    "1xbet", "888sports", "bet365", "betfair", "betsson", "betway",
    "bwin", "grancasinomadrid", "casinomarbella", "codere", "daznbet",
    "goldenbull", "interwetten", "kirolbet", "luckia", "marcaapuestas",
    "paf", "retabet", "speedybet", "sportium", "versus", "williamhill",
    "winamax", "yosports",
])


def nk(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def cuotas(fid):
    out = {}
    for o in api("/odds", fixture=fid) or []:
        for bk in o["bookmakers"]:
            if nk(bk["name"]) not in CASAS:
                continue
            for b in bk["bets"]:
                if b["name"] == "Home Corners Over/Under":
                    lado = "H"
                elif b["name"] == "Away Corners Over/Under":
                    lado = "A"
                else:
                    continue
                for v in b["values"]:
                    t = v["value"].split()
                    if len(t) == 2 and t[0] == "Over":
                        k = (lado, float(t[1]))
                        d = out.setdefault(k, {})
                        c = float(v["odd"])
                        if c > d.get(bk["name"], 0):
                            d[bk["name"]] = c
    return out


memo = {}


def hist(tid):
    if tid not in memo:
        memo[tid] = historial(tid)
    return memo[tid]


hoy = datetime.now(MAD).date()
hasta = hoy + timedelta(days=DIAS)
rango = {"from": str(hoy), "to": str(hasta)}
res = []
for lid, (pais, liga) in LIGAS.items():
    fx = api("/fixtures", league=lid, season=TEMP, **rango) or []
    print(liga, len(fx), "partidos")
    for x in fx:
        if x["fixture"]["status"]["short"] != "NS":
            continue
        loc = x["teams"]["home"]
        vis = x["teams"]["away"]
        cu = cuotas(x["fixture"]["id"])
        if not cu:
            continue
        hl = hist(loc["id"])
        hv = hist(vis["id"])
        if len(hl) < 14 or len(hv) < 14:
            continue
        dt = datetime.fromisoformat(x["fixture"]["date"]).astimezone(MAD)
        for (lado, ln), q in sorted(cu.items()):
            es_local = lado == "H"
            eq = loc if es_local else vis
            h = hl if es_local else hv
            ho = hv if es_local else hl
            r = analizar(h, ho, ln, es_local)
            if r["hits"] < 0.7 * r["n"] or max(q.values()) < 1.40:
                continue
            nombre = eq["name"] + " +" + str(ln).replace(".", ",")
            res.append({
                "pais": pais,
                "liga": liga,
                "fixture": x["fixture"]["id"],
                "equipo": eq["name"],
                "linea": ln,
                "local": loc["name"],
                "visitante": vis["name"],
                "hora": dt.strftime("%d/%m %H:%M"),
                "suceso": nombre + " córners",
                "l20": r["l20"],
                "cond": r["cond"],
                "condTxt": "local" if es_local else "visitante",
                "rival": r["rival"],
                "prob": r["prob"],
                "cuotas": [{"b": b, "c": c} for b, c in q.items()],
            })

ahora = datetime.now(MAD).isoformat(timespec="minutes")
out = {"updated_at": ahora, "days": [{"fecha": str(hoy), "candidatos": res}]}
json.dump(out, open("radar-data.json", "w"), ensure_ascii=False)
print(len(res), "selecciones;", gasto[0], "peticiones")
