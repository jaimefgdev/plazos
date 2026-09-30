import html, json, re
from comun import LOC, OUT, fechas
from ine import buscar, buscar_aprox, buscar_prefijo

raw = (LOC / "sal2.html").read_text(encoding="utf-8")
raw = raw.encode().decode("unicode_escape", errors="ignore").encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
t = html.unescape(re.sub(r"<br\s*/?>|</p>", "\n", raw))
t = re.sub(r"<[^>]+>", "\n", t)
regs, sin = [], []
vistos = set()
for l in t.split("\n"):
    l = l.strip()
    m = re.match(r"^([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ ().,'-]{2,60}?)\s+(\d.*)$", l)
    if not m or not fechas(m.group(2)):
        continue
    n = m.group(1).strip()
    ine = buscar(n, "CL", "Salamanca") or buscar_prefijo(n, "CL", "Salamanca") or buscar_aprox(n, "CL", "Salamanca")
    if not ine:
        sin.append(n); continue
    if ine["codigo"] in vistos:
        continue
    vistos.add(ine["codigo"])
    regs.append({"nombre": ine["NOMBRE"], "provincia": "Salamanca", "ine": ine["codigo"], "dias": fechas(m.group(2)), "parciales": []})
json.dump(regs, open(OUT / "CL_salamanca2.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(regs), "sin INE:", sin, [r for r in regs if r["nombre"] == "Salamanca"])
