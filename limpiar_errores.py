"""Limpieza puntual del registro de errores de cuota (errores.json).
Quita los errores falsos de remates / tiros a puerta que entraron cuando Sportium y Marca
tenian la tabla plegada y el bot leyo la tabla de otro mercado (asistencias).
Casos: Juventus-Venezia (Sportium, 20/11 11:20), Racing-Real Sociedad y Osasuna-Malaga (Marca, 20/11 18:29)."""
import json
import sys

ARCH = sys.argv[1] if len(sys.argv) > 1 else "errores.json"
# (casa, prefijo de la hora en que entraron, equipos locales afectados)
QUITAR = [
    ("Sportium", "2026-11-20T11:20", {"Juventus"}),
    ("Marcaapuestas", "2026-11-20T18:29", {"Racing Santander", "Osasuna"}),
]
MERCADOS = {"shots", "sot"}

d = json.load(open(ARCH, encoding="utf-8"))
sel = d.get("sel", {})
borrar = []
for k, r in sel.items():
    if r.get("mercado") not in MERCADOS:
        continue
    p = r.get("primera") or {}
    for casa, pref, locales in QUITAR:
        if r.get("local") in locales and str(p.get("t", "")).startswith(pref) and p.get("casas") == [casa]:
            borrar.append(k)
            break
for k in borrar:
    del sel[k]
json.dump(d, open(ARCH, "w", encoding="utf-8"), ensure_ascii=False)
print("limpieza: errores falsos borrados", len(borrar), "| quedan", len(sel))
