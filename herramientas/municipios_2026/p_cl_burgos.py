"""Burgos: el anexo del BOP es una imagen; se lee con OCR (burgos_ocr.json)."""
import difflib
import json
import re

from comun import OUT
from generico import zonas_a_registro
from ine import REG, _ART, norm, variantes

llaves = {}
for r in REG:
    if r["provincia"] == "Burgos":
        for v in variantes(r["NOMBRE"]):
            llaves.setdefault(_ART.sub("", v).replace(" ", ""), r)


def casar(nombre):
    k = _ART.sub("", norm(nombre)).replace(" ", "")
    if k in llaves:
        return llaves[k]
    m = difflib.get_close_matches(k, list(llaves), n=1, cutoff=0.88)
    return llaves[m[0]] if m else None


def leer(fichero):
    filas = json.load(open(OUT / fichero, encoding="utf-8"))

    # Nombres (columna izquierda) y fechas (columna central) por página.
    nombres, fechas_ = {}, []
    for p, y, x, t, c in filas:
        if x < 690:
            nombres.setdefault(p, []).append([y, x, t])
        elif x < 900 and re.search(r"\d{1,2}/\d{1,2}/2026", t):
            fechas_.append((p, y, t))
    filas_nombre = {}
    for p, lista in nombres.items():
        lista.sort()
        juntas = []
        for y, x, t in lista:
            if juntas and abs(juntas[-1][0] - y) < 8:  # trozos del mismo nombre en una fila
                juntas[-1][2] += " " + t
            else:
                juntas.append([y, x, t])
        filas_nombre[p] = juntas
    # Cada fecha va con el nombre más cercano en vertical.
    por_nombre = {}
    for p, y, t in fechas_:
        cand = min(filas_nombre.get(p, []), key=lambda n: abs(n[0] - y), default=None)
        if cand and abs(cand[0] - y) < 20:
            por_nombre.setdefault((p, cand[0], cand[2]), []).append(t)


    datos, sin = {}, set()
    for (p, _, nombre), fs in sorted(por_nombre.items()):
        ent = re.match(r"^(.*?)\s*\((?:AYTO\.?\s*)?([^)]+)\)\s*$", nombre)
        if ent and ent.group(2).strip().upper() in ("LA", "LAS", "LOS", "EL"):
            nombre, ent = f"{ent.group(2)} {ent.group(1)}", None
        zona = ""
        if ent:  # «CASTRILLO DE MURCIA (SASAMON)»: entidad local menor del municipio entre paréntesis
            zona, nombre = ent.group(1).strip() or "(entidad sin nombre legible)", ent.group(2)
        r = casar(nombre)
        if not r:
            sin.add(nombre)
            continue
        z = datos.setdefault(r["codigo"], {"nombre": r["NOMBRE"], "ine": r["codigo"], "zonas": {}})["zonas"]
        for fecha in fs:
            d, m = re.search(r"(\d{1,2})/(\d{1,2})/2026", fecha).groups()
            iso = f"2026-{int(m):02d}-{int(d):02d}"
            z.setdefault(zona, [])
            if iso not in z[zona]:
                z[zona].append(iso)


    return datos, sin


datos, sin = leer("burgos_ocr.json")
comp, sin2 = leer("burgos2_ocr.json")
print("complementaria:", len(comp), "municipios; ya estaban:", sum(k in datos for k in comp), "sin casar:", sorted(sin2)[:10])
datos.update(comp)
regs = []
for d in datos.values():
    r = zonas_a_registro(d["nombre"], "Burgos", d["zonas"])
    r["ine"] = d["ine"]
    regs.append(r)
json.dump(regs, open(OUT / "CL_burgos.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"burgos: {len(regs)} | sin casar: {sorted(sin)[:20]}")
print(">2:", [(r["nombre"], r["dias"]) for r in regs if len(r["dias"]) > 2])
