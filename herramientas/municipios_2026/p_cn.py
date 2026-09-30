import html, re
from comun import LOC, fechas, guardar, nombre

t = html.unescape(re.sub(r"<[^>]+>", "\n", (LOC / "can.html").read_text(encoding="utf-8")))
t = re.sub(r"\s*\n\s*", "\n", t)
t = t[t.index("RELACIÓN DE FIESTAS LOCALES PARA EL AÑO 2026"):]
ls = t.split("\n")[1:]
regs, actual = [], None
for l in ls:
    if re.match(r"^\d", l) and fechas(l):
        actual["dias"] += [f for f in fechas(l) if f not in actual["dias"]]
    elif re.fullmatch(r"[A-ZÁÉÍÓÚÑÜ .'\-]+\.?", l) and len(l) > 2:
        actual = {"nombre": nombre(l.rstrip(".")), "provincia": None, "dias": []}
        regs.append(actual)
    elif actual is None:
        continue
    elif regs and not fechas(l) and len(regs) > 80 and not actual["dias"]:
        break
guardar("CN", regs, "BOC n.º 165, de 21-8-2025 (Orden de 6-8-2025)")
print([ (r["nombre"], r["dias"]) for r in regs if len(r["dias"]) != 2])
