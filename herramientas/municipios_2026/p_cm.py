import json, re
from comun import OUT, lineas
from simple import parse

PROVS = ["Albacete", "Ciudad Real", "Cuenca", "Guadalajara", "Toledo"]
def prov(l):
    m = re.match(r"(?:Relación de Fiestas Locales de|Provincia de)\s+(.+)$", l.strip())
    return m.group(1).strip() if m and m.group(1).strip() in PROVS else None
ruido = lambda l: bool(re.match(r"^(Toledo, \d|La Directora|Trabajo y Econom|ANA MAR|AÑO XLI|\d{1,2} de \w+ de 202\d$|\d{4,5}$|Municipios|Fiestas$)", l.strip()))
aprox = []
regs, sin = parse(lineas("clm.txt"), "CM", prov, ruido, informe=aprox)
print("APROX:", aprox)
mod, sin2 = parse(lineas("clmmod.txt"), "CM", prov, ruido)
por = {r["ine"]: r for r in regs}
for r in mod:
    print("modificado:", r["nombre"], por.get(r["ine"], {}).get("dias"), "->", r["dias"])
    por[r["ine"]] = r
regs = list(por.values())
for r in regs:
    r["ccaa"] = "CM"
json.dump(regs, open(OUT / "CM.json", "w", encoding="utf-8"), ensure_ascii=False)
from collections import Counter
print(f"CM: {len(regs)} {Counter(r['provincia'] for r in regs)} | sin INE: {len(sin)} {sin[:15]} | sin días: {[r['nombre'] for r in regs if not r['dias']]} | >2: {[(r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2][:5]}")
