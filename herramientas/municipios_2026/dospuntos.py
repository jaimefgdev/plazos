"""Lector para listas «NOMBRE: fechas» (municipios en mayúsculas, entidades en minúsculas)."""
import re
from comun import fechas
from generico import zonas_a_registro
from ine import buscar, buscar_aprox, buscar_prefijo


def parse(ls, ccaa, provincia, stop=None):
    entradas = []
    # «MONTEAGUDO DE LAS VICARÍAS» / «: 25 de agosto…» y «RENIEBLAS; 5 de febrero…»
    unidas = []
    for l in ls:
        l = l.strip()
        if l.startswith(":") and unidas:
            unidas[-1] += " " + l
        else:
            unidas.append(re.sub(r"^([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ .()'-]{2,60});\s*(?=\d)", r"\1: ", l))
    for l in unidas:
        if not l:
            continue
        if stop and stop(l):
            break
        m = re.match(r"^([^:\d]{2,70}):\s*(.*)$", l)
        if m:
            entradas.append([m.group(1).strip(), m.group(2)])
        elif entradas and fechas(l) and not re.match(r"^(Núm\.|Pág\.|BOPSO)", l):
            entradas[-1][1] += " " + l
    regs, actual, sin = [], None, []
    for clave, texto in entradas:
        if clave.lower().startswith("para todo el municipio"):
            if actual:
                for z in actual["zonas"].values():
                    z += fechas(texto)
                actual["todo"] += fechas(texto)
            continue
        if clave.isupper():
            ine = buscar(clave, ccaa, provincia) or buscar_prefijo(clave, ccaa, provincia) or buscar_aprox(clave, ccaa, provincia)
            if not ine:
                sin.append(clave)
                actual = None
                continue
            actual = {"nombre": ine["NOMBRE"], "ine": ine["codigo"], "zonas": {"": fechas(texto)}, "todo": []}
            regs.append(actual)
        elif actual:
            actual["zonas"][clave] = fechas(texto) + actual["todo"]
    out = []
    for a in regs:
        r = zonas_a_registro(a["nombre"], provincia, a["zonas"])
        r["ine"] = a["ine"]
        out.append(r)
    return out, sin
