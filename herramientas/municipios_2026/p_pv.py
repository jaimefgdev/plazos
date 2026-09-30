import json, re
from comun import OUT, fechas, lineas
from generico import parse

def tramo(f, inicio, fin=None):
    ls = lineas(f)
    i = next(k for k, l in enumerate(ls) if inicio(l))
    j = next((k for k, l in enumerate(ls) if k > i and fin and fin(l)), len(ls))
    return ls[i:j]

todos = []
# Álava (BOTHA n.º 82): una fiesta por municipio + 28 de abril (San Prudencio) en todo el territorio.
ala, s1 = parse(tramo("ala.txt", lambda l: l == "DÍAS DE FIESTA DE CARÁCTER LOCAL", lambda l: l.startswith("Vitoria-Gasteiz, 14 de julio")),
                "PV", "Araba/Álava", mayus_modo=False, zonas_minusculas=False, ignora_desconocidos=True)
for r in ala: r["dias"].append("2026-04-28")
# Bizkaia (BOB n.º 138; modificación de Bilbao en el BOB n.º 148): + 31 de julio (San Ignacio).
biz_ls = [re.sub(r"^[•\-]\s*", "", l) for l in tramo("biz.txt", lambda l: "Por otro lado" in l, lambda l: l.startswith("En Bilbao, a 11"))]
biz, s2 = parse(biz_ls, "PV", "Bizkaia", mayus_modo=False, zonas_minusculas=False, ignora_desconocidos=True)
for r in biz:
    if r["nombre"] == "Bilbao":
        r["dias"] = ["2026-08-28"]
    r["dias"].append("2026-07-31")
# Gipuzkoa (BOG n.º 168): versión en castellano, municipios en mayúsculas + 31 de julio.
gi_ls = lineas("gip.txt")
i = [k for k, l in enumerate(gi_ls) if l.startswith("ABALTZISKETA")][-1]
gip, s3 = parse(gi_ls[i:], "PV", "Gipuzkoa")
for r in gip:
    if "2026-07-31" not in r["dias"]:
        r["dias"].append("2026-07-31")
for lote in (ala, biz, gip):
    for r in lote:
        r["ccaa"] = "PV"
        r["dias"] = sorted(set(r["dias"]))
        todos.append(r)
json.dump(todos, open(OUT / "PV.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"PV: Álava {len(ala)} Bizkaia {len(biz)} Gipuzkoa {len(gip)} | sin INE: {s1[:5]} {s2[:5]} {s3[:5]} | >2: {[(r['nombre'], r['dias']) for r in todos if len(r['dias']) > 2][:6]}")
print([(r["nombre"], r["dias"], r["parciales"]) for r in todos if r["nombre"] in ("Vitoria-Gasteiz", "Bilbao", "Donostia/San Sebastián")])
