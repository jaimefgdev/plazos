"""Zamora: el PDF es una tabla de tres columnas (localidad, día y mes, denominación)."""
import json, warnings
import pymupdf
from comun import LOC, OUT, fechas
from generico import zonas_a_registro
from ine import buscar, buscar_aprox, buscar_prefijo

warnings.filterwarnings("ignore")
import sys
ENTRADA, SALIDA = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("cyl_zamora.pdf", "CL_zamora.json")
doc = pymupdf.open(LOC / ENTRADA)
filas = []  # (página, y, columna, texto)
dentro = False
for np, page in enumerate(doc):
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t:
                continue
            if t.lower().startswith("denominaci"):
                dentro = True
                continue
            if dentro and t.lower().startswith(("zamora, a ", "la jefe de la oficina")):
                dentro = False
            if dentro:
                x = l["bbox"][0]
                col = "nombre" if x < 200 else ("fecha" if x < 360 else "desc")
                filas.append((np, round(l["bbox"][1] / 5), {"nombre": 0, "fecha": 1, "desc": 2}[col], col, t))
filas.sort()
filas = [(np, y * 5, col, t) for np, y, _, col, t in filas]
regs, actual, zona, sin, ultimo_nombre = [], None, "", [], None
for np, y, col, t in filas:
    if col == "nombre":
        if ultimo_nombre and ultimo_nombre[0] == np and y - ultimo_nombre[1] <= 15 and not ultimo_nombre[2]:
            # nombre partido en dos líneas: rehacer el registro
            t = ultimo_nombre[3] + " " + t
            if zona and zona == ultimo_nombre[3].lstrip("- "):
                actual["zonas"].pop(zona, None)
            elif actual and actual.get("_txt") == ultimo_nombre[3]:
                regs.pop(); actual = regs[-1] if regs else None
        ultimo_nombre = [np, y, False, t]
        if t.startswith("-"):
            zona = t.lstrip("- ").strip()
            if actual is not None:
                actual["zonas"].setdefault(zona, [])
            continue
        ine = buscar(t, "CL", "Zamora") or buscar_prefijo(t, "CL", "Zamora") or buscar_aprox(t, "CL", "Zamora", 0.85)
        if not ine:
            sin.append(t); zona = None; continue
        actual = {"nombre": ine["NOMBRE"], "ine": ine["codigo"], "zonas": {"": []}, "_txt": t}
        regs.append(actual); zona = ""
    elif col == "fecha":
        if ultimo_nombre:
            ultimo_nombre[2] = True
        if actual is not None and zona is not None:
            actual["zonas"].setdefault(zona, [])
            actual["zonas"][zona] += [f for f in fechas(t) if f not in actual["zonas"][zona]]
out = []
for a in regs:
    r = zonas_a_registro(a["nombre"], "Zamora", a["zonas"])
    r["ine"] = a["ine"]
    out.append(r)
json.dump(out, open(OUT / SALIDA, "w", encoding="utf-8"), ensure_ascii=False)
print(f"zamora: {len(out)} | sin INE: {sin[:15]} | sin días: {sum(not r['dias'] for r in out)} | >2: {[(r['nombre'], r['dias']) for r in out if len(r['dias']) > 2]}")
print([(r["nombre"], r["dias"]) for r in out if r["nombre"] in ("Zamora", "Almeida de Sayago", "Entrala", "Cañizal", "Hiniesta, La")])
