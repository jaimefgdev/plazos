import re
from comun import fechas, guardar, lineas, nombre

ls = lineas("ast.txt")
i = next(k for k, l in enumerate(ls) if l == "OVIEDO")
fin = next(k for k, l in enumerate(ls) if l.startswith("En Oviedo, a 3 de junio"))
bloques, actual = [], None
for l in ls[i:fin]:
    if not l or l.startswith(("https://", "BOLETÍN OFICIAL", "núm. ", "Cód. ")) or re.fullmatch(r"\d/\d", l):
        continue
    f = fechas(l)
    if f and re.match(r"^\d", l):
        actual["fechas"].append([f[0], ""])
    elif l.upper() == l and re.search(r"[A-ZÁÉÍÓÚÑ]", l) and not re.search(r"\d", l):
        if actual and not actual["fechas"]:  # nombre partido en dos líneas («MUROS DE» / «NALÓN»)
            actual["nombre"] += " " + l
            continue
        actual = {"nombre": l, "fechas": []}
        bloques.append(actual)
    elif actual and actual["fechas"]:
        actual["fechas"][-1][1] = (actual["fechas"][-1][1] + " " + l).strip()

regs = []
for b in bloques:
    r = {"nombre": nombre(b["nombre"]), "provincia": "Asturias", "dias": [], "parciales": []}
    for f, desc in b["fechas"]:
        todo = len(b["fechas"]) <= 2 or (re.search(r"todo el", desc, re.I) and not re.search(r"excepto", desc, re.I))
        if todo:
            r["dias"].append(f)
        else:
            r["parciales"].append({"fecha": f, "ambito": desc})
    regs.append(r)
guardar("AS", regs, "BOPA n.º 114, de 16-6-2025 (Resolución de 3-6-2025)")
for r in regs:
    if r["parciales"]:
        print(r["nombre"], r["dias"], [(p["fecha"], p["ambito"][:50]) for p in r["parciales"]])
