import json, re
from collections import Counter
from comun import LOC, OUT, fechas
from generico import zonas_a_registro
from ine import buscar, buscar_aprox, buscar_prefijo

RE_ENTRADA = re.compile(r"^(\s*)([^\d,][^,]*(?:,\s*(?:el|la|els|les|l'|l’|la|les)\b)?),\s*(.+)$")


def entradas(texto):
    """[(sangría, nombre, resto)] uniendo líneas partidas."""
    out = []
    for l in texto.split("\n"):
        if not l.strip() or re.match(r"^(DL B|ISSN|https?://|Núm\. |CVE-|\d+/\d+\s*$|Diari Oficial)", l.strip()):
            continue
        m = RE_ENTRADA.match(l)
        if m and (fechas(m.group(3)) or "no formulada" in m.group(3)):
            out.append([len(m.group(1)), m.group(2).strip(), m.group(3)])
        elif out and not l.strip().isupper() and not out[-1][2].rstrip().endswith("."):
            out[-1][2] += " " + l.strip()
    return out


def nombre_real(n):
    m = re.fullmatch(r"(.+?),\s*(el|la|els|les|l'|l’)", n, re.I)
    if m:
        art = m.group(2)
        return f"{art}{'' if art.endswith(("'", '’')) else ' '}{m.group(1)}"
    return n


texto = (LOC / "cat.txt").read_text(encoding="utf-8")
texto = texto[texto.index("ALT CAMP"):]
mods = {}
tmod = (LOC / "catmod.txt").read_text(encoding="utf-8")
for bloque in re.findall(r"ha de dir:\s*“(.*?)”", tmod, re.S):
    for _, n, resto in entradas(bloque):
        mods[nombre_real(n)] = fechas(resto)
regs, actual, sin = {}, None, []
for sangria, n, resto in entradas(texto):
    nr = nombre_real(n)
    if sangria == 0:
        ine = buscar(nr, "CT") or buscar(n, "CT") or buscar_aprox(nr, "CT", None, 0.92)
        for pv in ("Barcelona", "Girona", "Lleida", "Tarragona"):
            ine = ine or buscar_prefijo(nr, "CT", pv) or buscar_prefijo(nr.replace("-", " "), "CT", pv)
        if not ine:
            sin.append(nr); actual = None; continue
        dias = mods.pop(nr, None) or fechas(resto)
        actual = regs[ine["codigo"]] = {"nombre": ine["NOMBRE"], "provincia": ine["provincia"], "ine": ine["codigo"], "zonas": {"": dias}}
    elif actual is not None:
        actual["zonas"][nr] = fechas(resto)
print("modificaciones no aplicadas:", mods)
out = []
for a in regs.values():
    r = zonas_a_registro(a["nombre"], a["provincia"], a["zonas"])
    r.update(ine=a["ine"], ccaa="CT")
    out.append(r)
json.dump(out, open(OUT / "CT.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"CT: {len(out)} {Counter(r['provincia'] for r in out)} | sin INE: {len(sin)} {sin[:20]} | sin días: {len([r for r in out if not r['dias']])} | >2: {[(r['nombre'], r['dias']) for r in out if len(r['dias']) > 2][:5]}")
print([(r["nombre"], r["dias"], r["parciales"]) for r in out if r["nombre"] in ("Barcelona", "Lleida", "Girona", "Tarragona", "Sitges", "Viladecans")])
