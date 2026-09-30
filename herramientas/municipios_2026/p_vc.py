import json, re
from collections import Counter
from comun import LOC, OUT, fechas
from generico import zonas_a_registro
from ine import buscar, buscar_aprox, buscar_prefijo

PROV = {"ALICANTE": "Alicante/Alacant", "CASTELLÓN": "Castellón/Castelló", "CASTELLON": "Castellón/Castelló",
        "VALENCIA": "Valencia/València"}
CABEZA = re.compile(r"^([^\d:«»]{2,95}?)\s*:\s*(.*)$")


def entradas(cuerpo):
    out = []
    for l in cuerpo.split("\n"):
        l = l.strip()
        if not l or re.match(r"^(Núm\. \d|CVE:|https?://|\d+ / \d+$)", l):
            continue
        m = CABEZA.match(l)
        if m and sum(c.isupper() for c in m.group(1)) >= 3:
            out.append([m.group(1).strip(), m.group(2)])
        elif out:
            out[-1][1] += " " + l
    return out


def leer(texto):
    res = []
    partes = re.split(r"(?:RELACIÓN DE FIESTAS LOCALES EN LA PROVINCIA DE|Relación de fiestas locales 2026 en la provincia de)\s+(\w+)", texto, flags=re.I)
    for p, cuerpo in zip(partes[1::2], partes[2::2]):
        prov = PROV[p.upper()]
        res += [(prov, n, resto) for n, resto in entradas(cuerpo)]
    return res


t = (LOC / "val.txt").read_text(encoding="utf-8")
base = leer(t)
# Modificación (DOGV n.º 10281): cada «Debe decir «NOMBRE: …»» sustituye a la entrada.
tm = (LOC / "valmod.txt").read_text(encoding="utf-8")
mods = {}
for prov_txt, bloque in re.findall(r"provincia de (\w+):(.*?)(?=Relación de fiestas|\Z)", tm, re.S):
    for dd in re.findall(r"Debe decir:?\s*«(.*?)»", bloque, re.S):
        n, resto = dd.split(":", 1)
        mods[(PROV[prov_txt.upper()], n.strip())] = " ".join(resto.split())
print("modificaciones:", mods)
regs, sin, entidades = {}, [], []
for prov, n, resto in base:
    resto = mods.pop((prov, n), resto)
    n2 = n.replace("´", "'").replace("’", "'")
    dep = re.search(r"(?:Eatim|entidad local menor)?.*?dependiente de\s+(.+)$", n2, re.I)
    if dep:
        nombre_ent = re.split(r",?\s*(?:Eatim|entidad local menor)", n2, flags=re.I)[0].replace("Eatim de", "").strip(" ,") or n2
        entidades.append((prov, dep.group(1).strip(), nombre_ent, fechas(resto)))
        continue
    if "SIN DETERMINAR" in resto.upper():
        continue
    ine = buscar(n2, "VC", prov) or buscar_prefijo(n2, "VC", prov) or buscar_aprox(n2, "VC", prov, 0.92)
    if not ine:
        sin.append(n); continue
    regs[ine["codigo"]] = {"nombre": ine["NOMBRE"], "provincia": prov, "ine": ine["codigo"], "zonas": {"": fechas(resto)}}
print("modificaciones sin aplicar:", mods)
for prov, muni, ent, fs in entidades:
    ine = buscar(muni, "VC", prov) or buscar_aprox(muni, "VC", prov, 0.9)
    if ine and ine["codigo"] in regs:
        regs[ine["codigo"]]["zonas"][ent] = fs
    else:
        sin.append(f"{ent} (de {muni})")
out = []
for a in regs.values():
    r = zonas_a_registro(a["nombre"], a["provincia"], a["zonas"])
    r.update(ine=a["ine"], ccaa="VC")
    out.append(r)
json.dump(out, open(OUT / "VC.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"VC: {len(out)} {Counter(r['provincia'] for r in out)} | sin INE: {len(sin)} {sin[:20]} | >2: {[(r['nombre'], r['dias']) for r in out if len(r['dias']) > 2][:8]} | sin días: {[r['nombre'] for r in out if not r['dias']][:10]}")
print([(r["nombre"], r["dias"], r["parciales"]) for r in out if r["nombre"] in ("Dénia", "Alborache", "Alcosser", "Onil", "Benissoda", "Hondón de los Frailes")])
