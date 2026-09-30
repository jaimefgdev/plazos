import json, re
from comun import LOC, OUT, fechas
from ine import buscar, buscar_prefijo

t = (LOC / "rio.txt").read_text(encoding="utf-8").replace("\uffff", " ")
t = t[t.index("Logroño a 14 de agosto") - 20000 if False else 0:]
regs, sin = {}, []
for l in re.sub(r"\n(?![A-ZÁÉÍÓÚÑ][^:\n]{1,60}:)", " ", t).split("\n"):
    m = re.match(r"^([A-ZÁÉÍÓÚÑ][^:]{1,60}):\s*(.+)$", l.strip())
    if not m or not fechas(m.group(2)):
        continue
    n = m.group(1).strip()
    ine = buscar(n, "RI") or buscar_prefijo(n, "RI", "La Rioja")
    if not ine:
        sin.append(n); continue
    regs[ine["codigo"]] = {"nombre": ine["NOMBRE"], "provincia": "La Rioja", "ine": ine["codigo"], "dias": fechas(m.group(2)), "parciales": [], "ccaa": "RI"}
regs = list(regs.values())
json.dump(regs, open(OUT / "RI.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"RI: {len(regs)} | sin INE: {sin[:20]} | >2: {[(r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2][:5]} | sin días: {[r['nombre'] for r in regs if not r['dias']]}")
print([r for r in regs if r["nombre"] == "Logroño"])
