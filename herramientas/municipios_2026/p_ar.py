import re
from comun import fechas, guardar, lineas, nombre

CAB = re.compile(r"^(BOLETÍN OFICIAL DE ARAGÓN|\d{1,2} de \w+ de 202\d|Número \d+|csv: .*|\d{1,3})$")


def leer(fichero):
    ls = [l for l in lineas(fichero) if l and not CAB.match(l)]
    texto = "\n".join(ls)
    res = {}
    for bloque in re.split(r"provincia de (Huesca|Teruel|Zaragoza) para el año 2026\.", texto)[1:]:
        pass
    partes = re.split(r"provincia de (Huesca|Teruel|Zaragoza) para el año 2026\.", texto)
    for prov, cuerpo in zip(partes[1::2], partes[2::2]):
        # Cada entrada empieza por «- » (municipio) o «• » (entidad menor, se ignora).
        for m in re.finditer(r"(?ms)^([-•])\s*(.+?)(?=^[-•]\s|^Relación de días|\Z)", cuerpo):
            if m.group(1) != "-":
                continue
            ent = " ".join(m.group(2).split())
            nm = re.match(r"(.+?)\.\s", ent + " ")
            n = nombre(nm.group(1)) if nm else nombre(ent)
            res[(prov, n)] = fechas(ent[len(nm.group(1)) if nm else 0:])
    return res


base = leer("ara.txt")
comp = leer("ara2.txt")
cambios = [(k, base.get(k), v) for k, v in comp.items() if k in base and base[k] != v]
print("complementaria:", len(comp), "nuevos:", sum(k not in base for k in comp), "cambiados:", cambios[:10])
base.update(comp)
regs = [{"nombre": n, "provincia": p, "dias": d} for (p, n), d in base.items()]
guardar("AR", regs, "BOA n.º 225, de 20-11-2025, y Resolución complementaria de 10-3-2026 (BOA n.º 56)")
