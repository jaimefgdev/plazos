import re
from comun import fechas, guardar, lineas, nombre

ls = lineas("bal.txt")
i = ls.index("2. Festes d'àmbit local")
ISLAS = {"Mallorca", "Menorca", "Eivissa", "Formentera"}
bloques, actual, zona = [], None, None
for l in ls[i + 1:]:
    if not l or l.startswith(("https://", "Núm. ", "Fascicle ")) or re.fullmatch(r"\d{1,2} de \w+ de 2025", l):
        continue
    if re.match(r"2\.\d\. Illa", l):
        continue
    f = fechas(l)
    if f and re.match(r"^\d", l):
        desc = l.split(":", 1)[1].strip() if ":" in l else ""
        actual["zonas"].setdefault(zona or "", []).append((f[0], desc))
    elif l.upper() == l and re.search(r"[A-ZÀ-Ü]", l):
        actual = {"nombre": l, "zonas": {}}
        zona = None
        bloques.append(actual)
    elif actual is not None:
        # Núcleo o parroquia con fiestas propias. El PDF parte a veces el nombre en dos
        # líneas y mete una fecha en medio: es continuación si empieza en minúscula o si
        # el nombre anterior acaba en preposición/artículo.
        cont = zona is not None and (re.match(r"(de|des|del|d')\b", l) or re.search(r"\b(de|sa|ses|des|i|d')$", zona))
        if cont:
            fechas_zona = actual["zonas"].pop(zona)
            zona = zona + " " + l
            actual["zonas"][zona] = fechas_zona
        else:
            zona = l
            actual["zonas"].setdefault(zona, [])

regs = []
for b in bloques:
    if b["nombre"] == "FORMENTERA":  # corrección del BOIB n.º 139
        b["zonas"] = {"": [("2026-07-25", "Sant Jaume, Diada de Formentera"), ("2026-12-03", "Sant Francesc Xavier")]}
    zonas = {k: v for k, v in b["zonas"].items() if v}
    r = {"nombre": nombre(b["nombre"]), "provincia": "Illes Balears", "dias": [], "parciales": []}
    if list(zonas) == [""]:
        r["dias"] = [f for f, _ in zonas[""]]
    else:
        comunes = set.intersection(*[{f for f, _ in v} for v in zonas.values()])
        r["dias"] = sorted(comunes)
        for z, v in zonas.items():
            for f, _ in v:
                if f not in comunes:
                    r["parciales"].append({"fecha": f, "ambito": z})
    regs.append(r)
guardar("IB", regs, "BOIB n.º 129, de 27-9-2025; correcciones en BOIB n.º 139 y 150")
for r in regs:
    if r["parciales"] or len(r["dias"]) != 2:
        print(r["nombre"], r["dias"], r["parciales"][:4])
