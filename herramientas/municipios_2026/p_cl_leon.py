import json, re
from comun import OUT, fechas, lineas, nombre
from ine import buscar, buscar_prefijo

def anexo(f):
    ls = lineas(f)
    i = next((i for i, l in enumerate(ls) if l.startswith("CALENDARIO DE FIESTAS LOCALES") or l.startswith("ANEXO")), None)
    return ls[i + 1:]


import sys
ls = anexo(sys.argv[1] if len(sys.argv) > 1 else "cyl_leon.txt")
entradas = []
for l in ls:
    if not l or l.startswith(("Página ", "CVE del", "Boletín núm.", "Verificable", "Veri")):
        continue
    m = re.match(r"^([^:]{2,60}):\s*(.*)$", l)
    if m and not re.match(r"^\d", l):
        entradas.append([m.group(1).strip(), m.group(2)])
    elif entradas:
        entradas[-1][1] += " " + l
mayus = sum(1 for k, _ in entradas if k.isupper()) > 3  # la complementaria pone los municipios en mayúsculas
regs, actual, no_ine = [], None, []
for clave, texto in entradas:
    if clave.startswith("Para todo el municipio"):
        actual["_todo"] += fechas(texto)
        continue
    m = re.match(r"Para todo el municipio:\s*(.*)", texto)
    ine = buscar(clave, "CL", "León") or buscar_prefijo(clave, "CL", "León")
    if mayus and not clave.isupper():
        ine = None
    if ine:
        actual = {"nombre": ine["NOMBRE"], "provincia": "León", "dias": [], "parciales": [], "_propia": [], "_todo": []}
        regs.append(actual)
        if m:
            actual["_todo"] += fechas(m.group(1))
        else:
            actual["_propia"] = fechas(texto)
    elif actual:
        actual["parciales"] += [{"fecha": f, "ambito": clave} for f in fechas(texto)]
for r in regs:
    if r["_todo"] or r["parciales"]:
        r["dias"] = r["_todo"]
        # La línea con el nombre del municipio es entonces la de su núcleo principal.
        r["parciales"] = [{"fecha": f, "ambito": r["nombre"] + " (núcleo)"} for f in r["_propia"]] + r["parciales"]
    else:
        r["dias"] = r["_propia"]
    del r["_propia"], r["_todo"]
json.dump(regs, open(OUT / (sys.argv[2] if len(sys.argv) > 2 else "CL_leon.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(regs), "municipios; sin días de todo el municipio:", sum(1 for r in regs if not r["dias"]))
print([r for r in regs if r["nombre"] in ("León", "Acebedo", "Arganza", "Almanza")])
