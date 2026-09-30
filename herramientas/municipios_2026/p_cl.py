import json, re, sys
from comun import OUT, lineas
from generico import parse

def desde(f, marca):
    ls = lineas(f)
    i = next(i for i, l in enumerate(ls) if marca(l))
    return ls[i + 1:]

CASOS = {
    "avila": ("Ávila", lambda l: l.startswith("Ávila, 16 de septiembre de 2025")),
    "palencia": ("Palencia", lambda l: l in ("A N E X O", "ANEXO")),
    "valladolid": ("Valladolid", lambda l: l == "ANEXO"),
    "segovia": ("Segovia", lambda l: l.startswith("FIESTAS LOCALES DE LA PROVINCIA DE SEGOVIA"), False),
    "salamanca": ("Salamanca", lambda l: l == "ANEXO"),
}
for n in sys.argv[1:] or CASOS:
    prov, marca, *opc = CASOS[n]
    ls = desde(f"cyl_{n}.txt", marca)
    # Fin del anexo: el siguiente anuncio del boletín.
    fin = next((i for i, l in enumerate(ls) if re.match(r"^(AYUNTAMIENTO DE|DIPUTACI[ÓO]N PROVINCIAL|ADMINISTRACI[ÓO]N (LOCAL|DE JUSTICIA|AUTON[ÓO]MICA)|E D I C T O)", l.strip(), re.I)), len(ls))
    regs, sin = parse(ls[:fin], "CL", prov, zonas_minusculas=opc[0] if opc else True)
    json.dump(regs, open(OUT / f"CL_{n}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{n}: {len(regs)} | sin INE: {len(sin)} {sin[:8]} | sin días: {sum(not r['dias'] for r in regs)} | parciales: {sum(bool(r['parciales']) for r in regs)} | >2: {[ (r['nombre'],r['dias']) for r in regs if len(r['dias'])>2][:3]}")

from generico import APROX
print("APROX:", APROX)
