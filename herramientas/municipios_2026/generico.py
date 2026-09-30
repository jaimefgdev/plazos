"""Lector genérico: «NOMBRE» en una línea y las fechas en las siguientes."""
import re
from comun import fechas
from pre import preparar
from ine import buscar, buscar_aprox, buscar_prefijo


APROX = []


def es_fecha(l: str) -> bool:
    return bool(re.match(r"^\d{1,2}(?:[\s./]|de)", l + " ", re.I)) and bool(fechas(l))


def zonas_a_registro(nombre, provincia, zonas):
    """zonas: {ámbito: [fechas]}; «» es el municipio entero o su núcleo."""
    zonas = {k: v for k, v in zonas.items() if v}
    r = {"nombre": nombre, "provincia": provincia, "dias": [], "parciales": []}
    if not zonas:
        return r
    if list(zonas) == [""]:
        r["dias"] = zonas[""]
        return r
    if zonas.get(""):
        # El municipio tiene fechas propias (su núcleo principal): son las del municipio y
        # las entidades menores con fiestas distintas quedan como parciales.
        r["dias"] = list(zonas[""])
        for z, v in zonas.items():
            for f in v:
                if z and f not in r["dias"]:
                    r["parciales"].append({"fecha": f, "ambito": z})
        return r
    comunes = set.intersection(*[set(v) for v in zonas.values()])
    r["dias"] = [f for f in next(iter(zonas.values())) if f in comunes]
    for z, v in zonas.items():
        for f in v:
            if f not in comunes:
                r["parciales"].append({"fecha": f, "ambito": z or f"{nombre} (núcleo)"})
    return r


def parse(ls, ccaa, provincia, stop=None, mayus_modo=True, zonas_minusculas=True, ignora_desconocidos=False):
    ls = preparar(ls)
    regs, actual, zona, sin_ine = [], None, "", []
    for k, l in enumerate(ls):
        if stop and stop(l):
            break
        sig = ls[k + 1] if k + 1 < len(ls) else ""
        if es_fecha(l):
            if actual is not None and zona is not None:
                actual["zonas"].setdefault(zona, [])
                actual["zonas"][zona] += [f for f in fechas(l) if f not in actual["zonas"][zona]]
            continue
        if not es_fecha(sig) or len(l) > 60 or re.search(r"\d", l):
            continue
        limpio = l.strip(" .:")
        anejo = bool(re.search(r"\(anejo\)|^[–-]\s|\s[–-]\s", limpio, re.I))
        if re.search(r"\s[–-]\s", limpio):
            limpio = re.split(r"\s[–-]\s", limpio, 1)[1]
        limpio = re.sub(r"\s*\(anejo\)", "", limpio, flags=re.I).lstrip("–- ").strip()
        ine = None if anejo else buscar(limpio, ccaa, provincia)
        if not ine and not anejo and k > 0 and not es_fecha(ls[k - 1]):
            # «MADRIGAL DE LAS ALTAS» + «TORRES»: nombre partido en dos líneas
            ine = buscar(ls[k - 1].strip(" .:") + " " + limpio, ccaa, provincia)
        if not ine and not anejo:
            ine = buscar_prefijo(limpio, ccaa, provincia) or buscar_aprox(limpio, ccaa, provincia)
            if ine:
                APROX.append((provincia, limpio, ine["NOMBRE"]))
        mayus = limpio.upper() == limpio
        if ine and (mayus or not mayus_modo):
            actual = {"nombre": ine["NOMBRE"], "ine": ine["codigo"], "zonas": {}}
            regs.append(actual)
            zona = ""
        elif actual is not None and (anejo or (zonas_minusculas and (not mayus or not mayus_modo))):
            zona = limpio
        elif mayus or anejo or ignora_desconocidos:
            sin_ine.append(limpio)
            zona = None
        else:
            continue  # descripción de la fiesta  # entidad que no sabemos a qué municipio pertenece: se ignora
        out = []
    for a in regs:
        r = zonas_a_registro(a["nombre"], provincia, a["zonas"])
        r["ine"] = a["ine"]
        out.append(r)
    return out, sin_ine
