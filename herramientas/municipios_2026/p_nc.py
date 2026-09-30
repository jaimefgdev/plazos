import html, json, re
from comun import LOC, OUT, fechas, lineas
from ine import buscar, buscar_aprox, buscar_prefijo
from simple import parse

ls = lineas("nav.txt")
i = next(k for k, l in enumerate(ls) if l.startswith("ANEXO.–FIESTAS LOCALES"))
ruido = lambda l: bool(re.match(r"^(Ver tabla|Anuncio - Bolet|https?://|\d+ de 43$|\d{2}/\d{2}/2025)", l))
# Muchas «localidades» son concejos: solo se aceptan coincidencias exactas con el INE, los
# municipios compuestos cuyo nombre empieza por la localidad y dos casos revisados a mano.
MANUAL = {"URROZVILLA": "Urroz-Villa", "ESPARZA (Salazar)": "Esparza de Salazar/Espartza Zaraitzu"}
COMPUESTOS = {"BIURRUN": "Biurrun-Olcoz", "TIEBAS": "Tiebas-Muruarte de Reta",
              "LIZOÁIN": "Lizoain-Arriasgoiti/Lizoainibar-Arriasgoiti"}


def casar(n, prov):
    return buscar(MANUAL.get(n) or COMPUESTOS.get(n) or n, "NC", "Navarra")


regs, sin = parse(ls[i + 1:], "NC", lambda l: "Navarra" if l == "LOCALIDAD" else None, ruido, casar=casar)
# Modificación: Resolución 765/2025 (BON n.º 1, de 2-1-2026).
raw = (LOC / "nav2.html").read_text(encoding="utf-8")
raw = raw.encode().decode("unicode_escape", errors="ignore").encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
t = html.unescape(re.sub(r"<[^>]+>", "\n", raw))
t = t[t.index("1.º Modificar"):t.index("2.º")]
por = {r["ine"]: r for r in regs}
for n, resto in re.findall(r"–\s*([^:\n]+):\s*([^\n]+)", t):
    ine = buscar(n.strip(), "NC")
    if ine and ine["codigo"] in por:
        print("modificado:", ine["NOMBRE"], por[ine["codigo"]]["dias"], "->", fechas(resto))
        por[ine["codigo"]]["dias"] = fechas(resto)
# El 3 de diciembre (San Francisco Javier) es fiesta local común a toda Navarra (Resolución 390/2025).
for r in por.values():
    r["ccaa"] = "NC"
    if "2026-12-03" not in r["dias"]:
        r["dias"].append("2026-12-03")
regs = list(por.values())
json.dump(regs, open(OUT / "NC.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"NC: {len(regs)} | localidades que no son municipio: {len(sin)} | >2: {[(r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2][:5]}")
print([r for r in regs if r["nombre"].startswith("Pamplona")])
