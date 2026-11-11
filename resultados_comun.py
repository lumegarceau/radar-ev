import json
import os
from rcommon import api


def alineacion(fid):
    f = "cache/L" + str(fid) + ".json"
    if os.path.exists(f):
        return json.load(open(f))
    r = api("/fixtures/lineups", fixture=fid)
    if not r:
        return None
    d = {"xi": {}, "sub": {}, "n": {}}
    for t in r:
        tid = str(t["team"]["id"])
        xi = t.get("startXI") or []
        sb = t.get("substitutes") or []
        d["xi"][tid] = [p["player"]["id"] for p in xi]
        d["sub"][tid] = [p["player"]["id"] for p in sb]
        for p in xi + sb:
            d["n"][str(p["player"]["id"])] = p["player"]["name"]
    ok = len(d["xi"]) == 2 and all(d["xi"].values())
    if not ok:
        return None
    json.dump(d, open(f, "w"))
    return d
