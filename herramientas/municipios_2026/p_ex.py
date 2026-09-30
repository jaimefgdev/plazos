import json, re
from collections import Counter
from comun import OUT, lineas
from simple import parse

def prov(l):
    m = re.match(r"La provincia de (Badajoz|Cáceres)\.?", l.strip())
    return m.group(1) if m else None
ls = [re.sub(r"\.-\s*$", "", l) for l in lineas("ext.txt")]
i = next(k for k, l in enumerate(ls) if l.startswith("CALENDARIO OFICIAL DE FIESTAS LOCALES"))
aprox = []
regs, sin = parse(ls[i:], "EX", prov, informe=aprox, ruido=lambda l: bool(re.match(r"^(NÚMERO \d|Jueves|DOE|\d{5}$)", l.strip())))
print("APROX:", aprox)
for r in regs: r["ccaa"] = "EX"
json.dump(regs, open(OUT / "EX.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"EX: {len(regs)} {Counter(r['provincia'] for r in regs)} | sin INE: {len(sin)} {sin[:15]} | sin días: {[r['nombre'] for r in regs if not r['dias']]} | >2: {[(r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2][:5]}")
