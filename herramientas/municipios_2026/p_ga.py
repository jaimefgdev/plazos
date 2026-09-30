import html, json, re
from collections import Counter
from comun import LOC, OUT, fechas
from ine import buscar, buscar_aprox, buscar_prefijo

t = html.unescape(re.sub(r"<[^>]+>", "\n", (LOC / "gal.html").read_text(encoding="utf-8")))
t = re.sub(r"\s*\n\s*", "\n", t)
regs, sin, prov = [], [], None
for l in t.split("\n"):
    m = re.match(r"^Provincia: (.+?)\.?$", l)
    if m:
        prov = {"A Coruña": "A Coruña", "Lugo": "Lugo", "Ourense": "Ourense", "Pontevedra": "Pontevedra"}.get(m.group(1).strip())
        continue
    m = re.match(r"^\d+\.\s*([^:]+):\s*(.*)$", l)
    if not m or not prov:
        continue
    n, resto = m.group(1).strip(), m.group(2)
    ine = buscar(n, "GA", prov) or buscar_prefijo(n, "GA", prov) or buscar_aprox(n, "GA", prov)
    if not ine:
        sin.append(n); continue
    regs.append({"nombre": ine["NOMBRE"], "provincia": prov, "ine": ine["codigo"], "dias": fechas(resto), "parciales": [], "ccaa": "GA"})
json.dump(regs, open(OUT / "GA.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"GA: {len(regs)} {Counter(r['provincia'] for r in regs)} | sin INE: {sin} | sin días: {[r['nombre'] for r in regs if not r['dias']]} | >2: {[(r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2][:8]}")
