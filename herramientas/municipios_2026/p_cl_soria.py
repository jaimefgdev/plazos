import json
from comun import OUT, lineas
from dospuntos import parse

ls = lineas("cyl_soria.txt")
i = ls.index("ANEXO")
regs, sin = parse(ls[i + 1:], "CL", "Soria", stop=lambda l: l.startswith(("Soria, ", "ADMINISTRACIÓN LOCAL")))
json.dump(regs, open(OUT / "CL_soria.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"soria: {len(regs)} | sin INE: {sin[:10]} | sin días: {sum(not r['dias'] for r in regs)} | parciales: {sum(bool(r['parciales']) for r in regs)} | >2: {[ (r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2]}")
print([r for r in regs if r['nombre'] in ('Soria', 'Adradas')])
