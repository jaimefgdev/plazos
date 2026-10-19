"""Complementos de las fiestas locales de 2026 (octubre de 2026).

Después de publicar `municipios_2026.json` (ensamblar.py) se revisaron uno a uno los 742
municipios que faltaban buscándolos en todos los boletines. Este script aplica lo encontrado
sobre el fichero ya publicado, con la misma fuente oficial que cada dato:

1. Cataluña: los municipios que en la Orden EMT/208/2025 solo tienen fiestas por núcleos
   (una línea con el nombre del municipio y debajo, sangrados, sus núcleos) no se habían leído,
   y esos núcleos se habían pegado al municipio anterior como fiestas «parciales». Se rehace la
   asignación de núcleos de toda Cataluña según la sangría de la orden.
2. Navarra: las fiestas de fecha móvil («Lunes de Pentecostés», «Tercer sábado de septiembre»…)
   se calculan para 2026.
3. Ávila: dos relaciones complementarias (BOP de 1-12-2025 y 4-2-2026), la modificación de
   Peguerinos (BOP de 24-4-2026) y dos líneas dobles del BOP n.º 186.
4. Municipios que el boletín marca como «no comunicado», «no comunicada» o «propuesta no
   formulada» (Palencia, Valladolid, Madrid, Cataluña): se añaden sin fiestas y con
   `estado = "no_comunicado"`.
5. Municipios que no figuran en ningún boletín de su provincia (ni en las complementarias):
   se añaden sin fiestas y con `estado = "no_publicado"`. Las fiestas locales solo existen si
   la autoridad laboral las fija y las publica (art. 46 del RD 2001/1983).

Los textos de los boletines están en `boletines/complementos/` (fuera de git, como el resto).

    python herramientas/municipios_2026/complementos.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
BOL = AQUI / "boletines" / "complementos"
DATOS = RAIZ / "src" / "plazos" / "datos" / "municipios_2026.json"
sys.path.insert(0, str(AQUI))
sys.stdout.reconfigure(encoding="utf-8")

from ine import REG, buscar, norm  # noqa: E402

MESES = {m: i + 1 for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
     "noviembre", "diciembre"])}


def texto(nombre: str) -> str:
    return (BOL / nombre).read_text(encoding="utf-8", errors="ignore")


def fechas(t: str, anio: int = 2026) -> list[str]:
    """«16 de febrero y 25 de agosto» / «2 febrero y 3 febrero» / «5 y 6 de octubre»."""
    out = []
    pend = []
    for num, mes in re.findall(r"(\d{1,2})(?:\s+de)?\s+(?:(" + "|".join(MESES) + r")\b)?", t.lower()):
        if mes:
            for n in pend + [num]:
                out.append(date(anio, MESES[mes], int(n)).isoformat())
            pend = []
        else:
            pend.append(num)
    return sorted(set(out))


# --- fechas móviles de 2026 ---------------------------------------------------------------------

def _pascua(y: int) -> date:
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    return date(y, (h + l_ - 7 * m + 114) // 31, (h + l_ - 7 * m + 114) % 31 + 1)


DIAS = {"lunes": 0, "martes": 1, "miércoles": 2, "jueves": 3, "viernes": 4, "sábado": 5, "domingo": 6}
ORD = {"primer": 1, "primero": 1, "segundo": 2, "tercer": 3, "tercero": 3, "cuarto": 4, "quinto": 5}


def enesimo(anio: int, mes: int, dia_sem: int, n: int) -> date:
    d = date(anio, mes, 1)
    d += timedelta((dia_sem - d.weekday()) % 7)
    return d + timedelta(7 * (n - 1))


def ultimo(anio: int, mes: int, dia_sem: int) -> date:
    d = date(anio + (mes == 12), mes % 12 + 1, 1) - timedelta(1)
    return d - timedelta((d.weekday() - dia_sem) % 7)


def movil(expr: str, anio: int = 2026) -> tuple[str | None, str | None]:
    """Fecha de una fiesta móvil y, si la lectura no es inequívoca, un aviso."""
    e = expr.strip().lower().rstrip(".")
    p = _pascua(anio)
    fijas = {
        "lunes de pentecostés": p + timedelta(50), "segundo día de pentecostés": p + timedelta(50),
        "festividad de la ascensión": p + timedelta(39), "lunes de carnaval": p - timedelta(48),
        "martes de carnaval": p - timedelta(47), "viernes de carnaval": p - timedelta(51),
    }
    if e in fijas:
        return fijas[e].isoformat(), None
    m = re.fullmatch(r"(primer|segundo|tercer|cuarto) (lunes|martes|miércoles|jueves|viernes|sábado|domingo) de (\w+)", e)
    if m:
        return enesimo(anio, MESES[m.group(3)], DIAS[m.group(2)], ORD[m.group(1)]).isoformat(), None
    m = re.fullmatch(r"último (\w+) de (\w+)", e)
    if m:
        return ultimo(anio, MESES[m.group(2)], DIAS[m.group(1)]).isoformat(), None
    m = re.fullmatch(r"(\w+) siguiente al (primer|segundo|tercer|cuarto) domingo de (\w+)", e)
    if m:
        dom = enesimo(anio, MESES[m.group(3)], 6, ORD[m.group(2)])
        return (dom + timedelta((DIAS[m.group(1)] - 6) % 7 or 7)).isoformat(), None
    m = re.fullmatch(r"(\w+) anterior al (primer|segundo|tercer|cuarto) domingo de (\w+)", e)
    if m:
        dom = enesimo(anio, MESES[m.group(3)], 6, ORD[m.group(2)])
        return (dom - timedelta((6 - DIAS[m.group(1)]) % 7 or 7)).isoformat(), None
    if e == "viernes de la semana siguiente a san lucas":
        # San Lucas es el 18 de octubre (domingo en 2026): el viernes de la semana siguiente es el 23.
        d = date(anio, 10, 18)
        lunes = d + timedelta(7 - d.weekday())
        return (lunes + timedelta(4)).isoformat(), (
            "la orden dice «viernes de la semana siguiente a San Lucas»: se ha tomado el 23 de "
            "octubre (San Lucas, el 18, cae en domingo)")
    return None, None


# --- 1. Cataluña ---------------------------------------------------------------------------------

def cataluna():
    """[(nombre, provincia, días propios, núcleos [(nombre, días)], no_formulada)] según la sangría."""
    lineas = texto("cat.txt").split("\n")
    empezado, actual, out = False, None, []
    prov = None                           # la orden va por comarcas: la provincia sale del INE
    for raw in lineas:
        s = raw.strip()
        if not s or s.startswith("www.") or re.fullmatch(r"\d+", s):
            continue
        if s.isupper() and len(s) > 3 and not re.search(r"\d", s):
            empezado = True               # cabecera de comarca
            actual = None
            continue
        if not empezado or s.startswith("Barcelona, 11 de diciembre"):
            continue
        sangrado = raw.startswith("  ")
        nf = "no formulada" in s.lower()
        m = re.match(r"(.+?),\s*(\d.+)$", s)
        nombre = (m.group(1) if m else re.sub(r",?\s*propuesta no formulada\.?", "", s)).strip().rstrip(".")
        dias = fechas(m.group(2)) if m else []
        if sangrado and actual is not None:
            actual[3].append((nombre, dias))
        else:
            actual = [nombre, prov, dias, [], nf]
            out.append(actual)
    return out


# Nombres de la orden (o de su transcripción) que no son los del INE.
ALIAS_CT = {"Bigues i Riells": "Bigues i Riells del Fai", "Pontones": "Pontons", "Josa i Tuixent": "Josa i Tuixén",
            "Calonge": "Calonge i Sant Antoni", "Esparraguera": "Esparreguera", "Casó de La Selva": "Cassà de la Selva",
            "Avellanes y Santa Linya, Les": "Avellanes i Santa Linya, Les", "Roselló": "Rosselló",
            "Brunyola": "Brunyola i Sant Martí Sapresa", "Riells y Viabrea": "Riells i Viabrea",
            "Masarac": "Masarac i Vilarnadal"}
# Municipios que cambió la Orden EMT/3/2026: ahí manda el dato publicado, que ya la aplica.
EMT_3_2026 = {"Polinyà", "Tavèrnoles", "Cardona", "Viladecans", "Tordera", "Torà", "Castelldefels",
              "Sant Joan Despí", "Balenyà", "Sitges"}


def aplicar_cataluna(por_ine, nuevos, informe):
    for nombre, prov, dias, nucleos, nf in cataluna():
        if nombre.startswith(("Disposición", "Esta Orden", "Miquel Sàmper", "Consejero")):
            continue
        r = buscar(ALIAS_CT.get(nombre, nombre), "CT")
        if r is None:
            informe.append(f"CT sin INE: {nombre} ({prov})")
            continue
        ine = r["codigo"]
        comunes = sorted(set.intersection(*(set(d) for _, d in nucleos))) if nucleos and not dias else []
        propios = dias or comunes
        parciales = sorted({(f, n) for n, ds in nucleos for f in ds if f not in propios})
        if ine in por_ine:
            m = por_ine[ine]
            if m["dias"] != propios and not nf and propios:
                if nombre in EMT_3_2026:
                    informe.append(f"CT modificado por la EMT/3/2026 (se deja): {m['nombre']} {m['dias']}")
                else:
                    informe.append(f"CT CORREGIDO: {m['nombre']} {m['dias']} -> {propios} (lo dice la orden)")
                    m["dias"] = propios
            m["parciales"] = [{"fecha": f, "ambito": n} for f, n in parciales]
        elif nf and not nucleos:
            nuevos.append(_registro(r, [], [], "CT", "no_comunicado"))
        elif propios or parciales:
            nuevos.append(_registro(r, propios, [{"fecha": f, "ambito": n} for f, n in parciales], "CT"))


def _registro(r, dias, parciales, fuente, estado=None):
    reg = {"ine": r["codigo"], "nombre": r["NOMBRE"], "ccaa": r["ccaa"], "provincia": r["provincia"],
           "dias": dias, "parciales": parciales, "fuente": fuente}
    if estado:
        reg["estado"] = estado
    return reg


# --- 2. Navarra ----------------------------------------------------------------------------------

# La orden pone los concejos con el nombre corto del valle o cendea: «ARDANAZ (Egüés)».
NC_ALIAS = {"Egüés": "Valle de Egüés/Eguesibar", "Olza": "Cendea de Olza/Oltza Zendea",
            "Ollo": "Valle de Ollo/Ollaran", "Yerri": "Valle de Yerri/Deierri", "Goñi": "Val de Goñi/Goñerri"}
NC_CONCEJOS = {"LABAIEN": "Beintza-Labaien"}


def aplicar_navarra(por_ine, nuevos, informe, avisos):
    lineas = [s.strip() for s in texto("nc241.txt").split("\n") if s.strip()]
    i0 = next(i for i, s in enumerate(lineas) if s == "LOCALIDAD")
    filas = []
    for a, b in zip(lineas[i0:], lineas[i0 + 1:]):
        if re.fullmatch(r"[A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ \-/'.]+(?: \(.+\))?", a) and not b.isupper():
            filas.append((a, b))
    por_mun: dict[str, list] = {}
    for loc, expr in filas:
        dias = fechas(expr)
        aviso = None
        if not dias:
            d, aviso = movil(expr)
            if d is None:
                continue
            dias = [d]
        m = re.fullmatch(r"(.+?) \((.+)\)", loc)
        concejo, mun = (m.group(1), m.group(2)) if m else (None, loc)
        if mun.upper() == mun and m:          # «NOÁIN (VALLE DE ELORZ)»: el municipio es lo de dentro
            concejo, mun = None, m.group(2)
        if loc in NC_CONCEJOS:                # concejo que la orden pone sin su municipio
            concejo, mun = loc, NC_CONCEJOS[loc]
        mun = NC_ALIAS.get(mun, mun)
        r = buscar(mun.title() if mun.isupper() else mun, "NC", "Navarra")
        if r is None:
            continue
        por_mun.setdefault(r["codigo"], [r, [], []])
        (por_mun[r["codigo"]][2] if concejo else por_mun[r["codigo"]][1]).extend(
            [(d, concejo.title()) for d in dias] if concejo else dias)
        if aviso:
            avisos[r["codigo"]] = aviso
    for ine, (r, propios, concejos) in por_mun.items():
        if ine in por_ine:
            m = por_ine[ine]
            ya = {(p["fecha"], p["ambito"]) for p in m["parciales"]}
            for d, c in concejos:
                if (d, c) not in ya and d not in m["dias"]:
                    m["parciales"].append({"fecha": d, "ambito": c})
            m["parciales"].sort(key=lambda p: (p["fecha"], p["ambito"]))
            continue
        dias = sorted(set(propios) | {"2026-12-03"})
        parciales = sorted({(d, c) for d, c in concejos if d not in dias})
        nuevos.append(_registro(r, dias, [{"fecha": d, "ambito": c} for d, c in parciales], "NC"))


# --- 3. Ávila --------------------------------------------------------------------------------------

AVILA = {  # de las dos relaciones complementarias, la modificación de abril y el BOP n.º 186
    "Barco de Ávila, El": ("2026-08-12", "2026-09-04"), "Barraco, El": ("2026-09-14", "2026-09-15"),
    "Hernansancho": ("2026-09-28", "2026-11-11"), "Horcajada, La": ("2026-09-28", "2026-09-29"),
    "Oso, El": ("2026-05-15", "2026-09-08"), "Adrada, La": ("2026-02-03", "2026-08-06"),
    "Bercial de Zapardiel": ("2026-02-02", "2026-02-03"), "Mamblas": ("2026-05-25", "2026-09-21"),
    "San Esteban de los Patos": ("2026-07-24", "2026-12-04"), "Peguerinos": ("2026-08-17", "2026-10-05"),
}


PARCIALES_AVILA = {  # BOP n.º 186: municipios que solo figuran por núcleos
    "San Juan de Gredos": {"La Herguijuela": ("2026-06-24", "2026-08-03"),
                           "Navacepeda de Tormes": ("2026-06-24", "2026-08-29"),
                           "San Bartolomé de Tormes": ("2026-08-24", "2026-09-15")},
    "Santiago del Tormes": {"Aliseda de Tormes": ("2026-07-20", "2026-07-24"),
                            "Horcajo de la Ribera": ("2026-07-22", "2026-07-24"),
                            "La Lastra del Cano": ("2026-10-02", "2026-10-05"),
                            "Navasequilla": ("2026-07-23", "2026-07-24")},
}
# BOP de León (relación de fiestas de 2026): La Vecilla figura por localidades.
# BOP de Palencia de 2026: Valde-Ucieza figura por localidades.
PARCIALES_PALENCIA = {"Valde-Ucieza": {"Robladillo de Ucieza": ("2026-09-08", "2026-11-30"),
                                       "Villasabariego de Ucieza": ("2026-08-10", "2026-12-14"),
                                       "Miñanes": ("2026-03-19", "2026-07-18"),
                                       "Villamorco": ("2026-05-15", "2026-12-26")}}
# BOCM: dos municipios con sus fechas que no se habían leído.
MADRID = {"Olmeda de las Fuentes": ("2026-04-06", "2026-08-24"),
          "Orusco de Tajuña": ("2026-09-14", "2026-12-28")}
PARCIALES_LEON = {"Vecilla, La": {"La Vecilla de Curueño": ("2026-01-28", "2026-06-08"),
                                  "Campohermoso": ("2026-01-07", "2026-07-25"),
                                  "La Cándana de Curueño": ("2026-08-07", "2026-12-14"),
                                  "Sopeña de Curueño": ("2026-01-19", "2026-09-08")}}


def por_nucleos(nucleos: dict) -> tuple[list[str], list[dict]]:
    """Días comunes a todos los núcleos (los del municipio) y el resto como parciales."""
    comunes = sorted(set.intersection(*(set(d) for d in nucleos.values())))
    parciales = sorted((f, n) for n, ds in nucleos.items() for f in ds if f not in comunes)
    return comunes, [{"fecha": f, "ambito": n} for f, n in parciales]


# --- Andalucía: BOJA n.º 247 de 2025 (altas y Coín) y n.º 32 de 2026 (Guarromán) -----------------

ANDALUCIA = {
    ("Almería", "Cóbdar"): ("2026-01-19", "2026-08-10"), ("Almería", "Garrucha"): ("2026-07-16", "2026-08-17"),
    ("Almería", "Oria"): ("2026-05-11", "2026-08-24"),
    ("Granada", "Alpujarra de la Sierra"): ("2026-01-02", "2026-09-29"), ("Granada", "Cádiar"): ("2026-10-02", "2026-10-05"),
    ("Granada", "Castril"): ("2026-10-05", "2026-10-08"), ("Granada", "Cogollos de Guadix"): ("2026-04-27", "2026-08-28"),
    ("Granada", "Moclín"): ("2026-01-16", "2026-10-05"), ("Granada", "Puebla de Don Fadrique"): ("2026-05-25", "2026-12-28"),
    ("Granada", "Villanueva de las Torres"): ("2026-02-03", "2026-08-03"),
    ("Jaén", "Baños de la Encina"): ("2026-05-11", "2026-10-30"), ("Jaén", "Cambil"): ("2026-02-23", "2026-05-22"),
    ("Jaén", "Carolina, La"): ("2026-05-15", "2026-11-24"), ("Jaén", "Porcuna"): ("2026-03-21", "2026-09-04"),
    ("Jaén", "Rus"): ("2026-02-03", "2026-09-23"),
    ("Málaga", "Pujerra"): ("2026-06-13", "2026-11-03"), ("Málaga", "Sayalonga"): ("2026-07-20", "2026-10-07"),
    # BOJA 197: «PÍÑAR» se había casado con El Pinar (la «ñ» se pierde al normalizar).
    ("Granada", "Píñar"): ("2026-05-04", "2026-06-12"),
}
CORRECCIONES = {  # (provincia, nombre): días que dice el boletín
    ("Jaén", "Guarromán"): ["2026-06-12", "2026-07-24"],      # BOJA n.º 32 de 2026
    ("Málaga", "Coín"): ["2026-05-04", "2026-06-01"],         # BOJA n.º 247 de 2025
    ("Granada", "Pinar, El"): ["2026-05-04", "2026-08-17"],   # BOJA n.º 197 de 2025
}


# --- País Vasco: BOTHA n.º 82, BOB n.º 138 y BOG n.º 168 de 2025 -----------------------------------

def ayala() -> list[dict]:
    """Concejos de Ayala/Aiara con su fiesta (BOTHA n.º 82, transcripción de la delegación)."""
    t = texto("al_sea.txt")
    bloque = t[t.index("AYALA:"):t.index("BAÑOS DE EBRO")]
    out = []
    for nombre, resto in re.findall(r"\n([A-ZÁÉÍÓÚÑ][^\n:\d]+?):?\s+(\d{1,2} de \w+)", bloque):
        out.append({"fecha": fechas(resto)[0], "ambito": nombre.strip()})
    assert len(out) == 24, len(out)
    return sorted(out, key=lambda p: (p["fecha"], p["ambito"]))


SAN_PRUDENCIO, SAN_IGNACIO = "2026-04-28", "2026-07-31"
PAIS_VASCO = {  # (provincia, nombre): (días, núcleos {nombre: fecha}, aviso)
    ("Araba/Álava", "Kripan"): ([SAN_PRUDENCIO, "2026-09-08"], {}, None),
    ("Araba/Álava", "Labastida/Bastida"): ([SAN_PRUDENCIO], {}, (
        "la resolución fija la segunda fiesta como «noviembre (2.º día de Acción de Gracias)», sin "
        "día concreto: confírmalo con el ayuntamiento")),
    ("Bizkaia", "Arrankudiaga-Zollo"): (["2026-06-29", SAN_IGNACIO], {}, None),
    ("Gipuzkoa", "Pasaia"): ([SAN_IGNACIO], {"Pasai Donibane": "2026-06-24", "Pasai San Pedro": "2026-06-29",
                                             "Pasai Antxo": "2026-07-07", "Trintxerpe": "2026-07-16"}, None),
    ("Gipuzkoa", "Bidania-Goiatz"): ([SAN_IGNACIO], {"Bidania": "2026-08-24", "Goiatz": "2026-08-14"}, None),
    ("Gipuzkoa", "Ezkio-Itsaso"): ([SAN_IGNACIO], {
        "Ezkio auzoa": "2026-05-08", "Santa Luzia-Anduaga auzoa": "2026-06-29",
        "Itsaso-Alegia auzoa": "2026-07-22", "Itsaso hirigunea": "2026-08-24",
        "Mendialdea Zozkera": "2026-09-08"}, None),
}


# --- 4 y 5. Sin fiestas: «no comunicado» y ausentes de todos los boletines ------------------------

def no_comunicados() -> dict[str, list[str]]:
    """Nombres marcados como no comunicados en el boletín, por clave de fuente."""
    out = {}
    pa = re.findall(r"\n([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ ,()'\-]+?)\s*\nNo comunicado\s*\n\s*No comunicado", texto("pa.txt"))
    # Tres que la expresión no recoge (minúsculas o nombre abreviado en el BOP).
    out["CL:Palencia"] = pa + ["Bustillo del Páramo de Carrión", "Lomas", "Vertavillo"]
    va = re.findall(r"\n([A-ZÁÉÍÓÚÑÜ][A-ZÁÉÍÓÚÑÜ ,()'\-]+?)\s*\nNo comunicada\s*\n\s*No comunicada", texto("ls_valladolid.txt"))
    out["CL:Valladolid"] = va
    out["MD"] = re.findall(r"— ([^:\n]+): no comunicado", texto("md.txt"))
    out["VC"] = ["Sacañet", "Vilanova d'Alcolea", "Paiporta"]     # DOGV: «SIN DETERMINAR»
    return out


def exacto(nombre: str, provincia: str) -> dict:
    """Municipio del INE por su nombre exacto (para los añadidos escritos a mano)."""
    r = [x for x in REG if x["NOMBRE"] == nombre and x["provincia"] == provincia]
    assert len(r) == 1, (nombre, provincia)
    return r[0]


def fuente_de(r) -> str:
    return f"CL:{r['provincia']}" if r["ccaa"] == "CL" else r["ccaa"]


def main() -> None:
    crudo = json.loads(DATOS.read_text(encoding="utf-8"))
    por_ine = {m["ine"]: m for m in crudo["municipios"]}
    nuevos, informe, avisos = [], [], {}
    antes = len(por_ine)

    aplicar_cataluna(por_ine, nuevos, informe)
    aplicar_navarra(por_ine, nuevos, informe, avisos)
    for nombre, dias in AVILA.items():
        r = buscar(nombre, "CL", "Ávila")
        if r and r["codigo"] not in por_ine:
            nuevos.append(_registro(r, list(dias), [], "CL:Ávila"))

    for prov, tabla in (("Ávila", PARCIALES_AVILA), ("León", PARCIALES_LEON), ("Palencia", PARCIALES_PALENCIA)):
        for nombre, nucleos in tabla.items():
            r = exacto(nombre, prov)
            if r["codigo"] not in por_ine:
                nuevos.append(_registro(r, *por_nucleos(nucleos), f"CL:{prov}"))
    r = exacto("Ciruelos de Cervera", "Burgos")
    if r["codigo"] not in por_ine:
        nuevos.append(_registro(r, ["2026-01-20", "2026-07-16"], [], "CL:Burgos"))
        avisos[r["codigo"]] = ("el BOP lo publica como «Ciruelos de Cervera (Ayto. Valdeande)», aunque es "
                               "un municipio propio")

    for nombre, dias in MADRID.items():
        r = exacto(nombre, "Madrid")
        if r["codigo"] not in por_ine:
            nuevos.append(_registro(r, list(dias), [], "MD"))
    for (prov, nombre), dias in ANDALUCIA.items():
        r = exacto(nombre, prov)
        if r["codigo"] not in por_ine:
            nuevos.append(_registro(r, list(dias), [], "AN"))
    for (prov, nombre), dias in CORRECCIONES.items():
        m = por_ine[exacto(nombre, prov)["codigo"]]
        if m["dias"] != dias:
            informe.append(f"CORREGIDO: {m['nombre']} {m['dias']} -> {dias}")
            m["dias"] = dias

    for (prov, nombre), (dias, nucleos, aviso) in PAIS_VASCO.items():
        r = exacto(nombre, prov)
        parciales = [{"fecha": f, "ambito": n} for n, f in sorted(nucleos.items(), key=lambda x: x[1])]
        if r["codigo"] not in por_ine:
            nuevos.append(_registro(r, dias, parciales, "PV"))
            if aviso:
                avisos[r["codigo"]] = aviso
    r = exacto("Ayala/Aiara", "Araba/Álava")
    if r["codigo"] not in por_ine:
        nuevos.append(_registro(r, [SAN_PRUDENCIO], ayala(), "PV"))

    ya = set(por_ine) | {n["ine"] for n in nuevos}
    for fuente, nombres in no_comunicados().items():
        ccaa, prov = {"MD": ("MD", "Madrid"), "VC": ("VC", None)}.get(fuente) or ("CL", fuente.split(":")[1])
        for n in nombres:
            r = buscar(n.title() if n.isupper() else n, ccaa, prov)
            if r and r["codigo"] not in ya:
                nuevos.append(_registro(r, [], [], fuente, "no_comunicado"))
                ya.add(r["codigo"])

    # 5. Los que siguen sin aparecer en ningún boletín de su provincia.
    faltan = json.loads((BOL / "faltan.json").read_text(encoding="utf-8"))
    for prov, lista in faltan.items():
        for ine, nombre in lista:
            if ine not in ya:
                r = next(x for x in REG if x["codigo"] == ine)
                nuevos.append(_registro(r, [], [], fuente_de(r), "no_publicado"))
                ya.add(ine)

    f = crudo["fuentes"]
    f["AN"]["texto"] = ("BOJA n.º 197, de 14-10-2025; modificaciones en BOJA n.º 247 de 2025 y n.º 32, 33 y 79 "
                        "de 2026")
    f["CL:Ávila"]["texto"] = ("BOP de Ávila n.º 186, de 26-9-2025; relaciones complementarias en los n.º 231, "
                              "de 1-12-2025, y 23, de 4-2-2026; modificación en el n.º 77, de 24-4-2026")

    for n in nuevos:
        if n["ine"] in avisos:
            n["aviso"] = avisos[n["ine"]]
        por_ine[n["ine"]] = n
    crudo["municipios"] = sorted(por_ine.values(), key=lambda m: m["ine"])
    print(f"antes {antes}, ahora {len(por_ine)} (+{len(por_ine) - antes})")
    for linea in informe:
        print(" ·", linea)
    if "--escribir" in sys.argv:
        DATOS.write_text(json.dumps(crudo, ensure_ascii=False, indent=None), encoding="utf-8", newline="\n")
        print("escrito", DATOS)
    else:
        json.dump(nuevos, open(BOL / "nuevos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
