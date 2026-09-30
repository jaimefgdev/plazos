import re
from comun import fechas, guardar, lineas, nombre

PROVS = ["ALMERÍA", "CÁDIZ", "CÓRDOBA", "GRANADA", "HUELVA", "JAÉN", "MÁLAGA", "SEVILLA"]
ls = lineas("and.txt")
i = ls.index("FIESTAS LOCALES DE ANDALUCÍA 2026") + 1
# Quitar cabeceras de página: desde la línea «00327114» hasta la URL del BOJA.
limpias, saltar = [], False
for l in ls[i:]:
    if l == "00327114":
        saltar = True
    if not saltar and l:
        limpias.append(l)
    if saltar and l.startswith("https://www.juntadeandalucia.es/eboja"):
        saltar = False
regs, prov, actual = [], None, None
for k, l in enumerate(limpias):
    f = fechas(l)
    if f:
        if actual is None:
            print("fecha sin municipio:", l); continue
        actual["dias"] += [x for x in f if x not in actual["dias"]]
        continue
    siguiente = limpias[k + 1] if k + 1 < len(limpias) else ""
    if l in PROVS and not fechas(siguiente):
        prov = l.title(); actual = None; continue
    actual = {"nombre": nombre(l), "provincia": prov, "dias": []}
    regs.append(actual)
# Modificaciones BOJA 33 y 79 de 2026.
MOD = {"Escacena del Campo": ["2026-06-01", "2026-08-17"], "Almogía": ["2026-04-06", "2026-05-11"], "Loja": ["2026-04-25", "2026-09-04"], "Guaro": ["2026-05-25", "2026-08-31"],
       "La Campana": ["2026-05-11", "2026-09-10"], "Los Molares": ["2026-05-15", "2026-07-29"],
       "Villaverde del Río": ["2026-06-01", "2026-09-08"]}
for r in regs:
    if r["nombre"] in MOD:
        r["dias"] = MOD.pop(r["nombre"])
assert not MOD, MOD
guardar("AN", regs, "BOJA n.º 197, de 14-10-2025; modificaciones en BOJA n.º 33 y 79 de 2026")
