"""Índice del diccionario de municipios del INE (1-1-2026) para casar nombres."""
import json, re, unicodedata
from pathlib import Path

AUTO = {"01": "AN", "02": "AR", "03": "AS", "04": "IB", "05": "CN", "06": "CB", "07": "CL", "08": "CM", "09": "CT",
        "10": "VC", "11": "EX", "12": "GA", "13": "MD", "14": "MC", "15": "NC", "16": "PV", "17": "RI", "18": "CE",
        "19": "ML"}
PROV = {"01": "Araba/Álava", "02": "Albacete", "03": "Alicante/Alacant", "04": "Almería", "05": "Ávila", "06": "Badajoz",
        "07": "Illes Balears", "08": "Barcelona", "09": "Burgos", "10": "Cáceres", "11": "Cádiz", "12": "Castellón/Castelló",
        "13": "Ciudad Real", "14": "Córdoba", "15": "A Coruña", "16": "Cuenca", "17": "Girona", "18": "Granada",
        "19": "Guadalajara", "20": "Gipuzkoa", "21": "Huelva", "22": "Huesca", "23": "Jaén", "24": "León", "25": "Lleida",
        "26": "La Rioja", "27": "Lugo", "28": "Madrid", "29": "Málaga", "30": "Murcia", "31": "Navarra", "32": "Ourense",
        "33": "Asturias", "34": "Palencia", "35": "Las Palmas", "36": "Pontevedra", "37": "Salamanca",
        "38": "Santa Cruz de Tenerife", "39": "Cantabria", "40": "Segovia", "41": "Sevilla", "42": "Soria", "43": "Tarragona",
        "44": "Teruel", "45": "Toledo", "46": "Valencia/València", "47": "Valladolid", "48": "Bizkaia", "49": "Zamora",
        "50": "Zaragoza", "51": "Ceuta", "52": "Melilla"}
ARTS = r"(el|la|los|las|l|els|les|o|a|os|as|lo|sa|ses|es|s|es)"

REG = json.load(open(Path(__file__).with_name("ine.json"), encoding="utf-8"))
for r in REG:
    r["ccaa"] = AUTO[r["CODAUTO"]]
    r["provincia"] = PROV[r["CPRO"]]
    r["codigo"] = r["CPRO"] + r["CMUN"]


def norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
    s = s.replace("’", "'").replace("`", "'")
    s = re.sub(r"[^a-z0-9ñç' ]+", " ", s)
    return " ".join(s.split())


def variantes(nombre: str) -> set[str]:
    out = set()
    for parte in re.split(r"\s*/\s*|\s+-\s+", nombre):
        p = parte.strip()
        m = re.fullmatch(r"(.+?),\s*(.+)", p) or re.fullmatch(r"(.+?)\s*\((.+)\)", p)
        if m and len(m.group(2).split()) <= 1:
            p2 = f"{m.group(2)} {m.group(1)}"
            out |= {norm(p2), norm(p2).replace("' ", "'")}
            out.add(norm(m.group(1)))
        base = norm(p)
        out |= {base, base.replace("' ", "'")}
        # «L'Hospitalet» ~ «L Hospitalet» ~ «Hospitalet»
        out.add(norm(p).replace("'", " "))
    out.add(norm(nombre))
    return {v for v in out if v}


IDX: dict[tuple[str, str], list[dict]] = {}
for r in REG:
    for v in variantes(r["NOMBRE"]):
        for ambito in (r["ccaa"], r["provincia"]):
            IDX.setdefault((ambito, v), []).append(r)


def buscar(nombre: str, ccaa: str, provincia: str | None = None) -> dict | None:
    for v in sorted(variantes(nombre), key=len, reverse=True):
        for ambito in ([provincia] if provincia else []) + [ccaa]:
            c = IDX.get((ambito, v), [])
            c = [x for x in c if x["ccaa"] == ccaa]
            uniq = {x["codigo"]: x for x in c}
            if len(uniq) == 1:
                return next(iter(uniq.values()))
    return None


def primaria(nombre: str) -> str:
    """Forma principal normalizada: «Vecilla, La» -> «la vecilla»."""
    p = re.split(r"\s*/\s*", nombre)[0]
    m = re.fullmatch(r"(.+?),\s*(.+)", p)
    return norm(f"{m.group(2)} {m.group(1)}" if m else p)


def buscar_prefijo(nombre: str, ccaa: str, provincia: str) -> dict | None:
    """«Carrizo de la Ribera» -> «Carrizo»; «Villagatón-Brañuelas» -> «Villagatón». Solo si es único."""
    n = norm(nombre)
    cand = [r for r in REG if r["ccaa"] == ccaa and r["provincia"] == provincia
            and (n.startswith(primaria(r["NOMBRE"]) + " ") or primaria(r["NOMBRE"]).startswith(n + " "))]
    return cand[0] if len(cand) == 1 else None


_ART = re.compile(r"^(el|la|los|las|l'|els|les|o|a|os|as|lo|sa|ses|es|s')\s*")
_orig_variantes = variantes


def variantes(nombre: str) -> set[str]:  # noqa: F811
    v = _orig_variantes(nombre)
    return v | {_ART.sub("", x) for x in v}


IDX.clear()
for r in REG:
    for v in variantes(r["NOMBRE"]):
        for ambito in (r["ccaa"], r["provincia"]):
            IDX.setdefault((ambito, v), []).append(r)


def buscar_aprox(nombre: str, ccaa: str, provincia: str | None, umbral: float = 0.88) -> dict | None:
    """Coincidencia aproximada (erratas, «Sta.» por «Santa», «Rio» por «Río»)."""
    import difflib
    n = norm(nombre).replace(" fdna", " fuentiduena").replace(" posadas", " de las posadas").replace(" vega serrezuela", " de la vega de la serrezuela").replace("sta ", "santa ").replace("sto ", "santo ").replace("ntra sra ", "nuestra senora ")
    n = _ART.sub("", n)
    cand = [r for r in REG if r["ccaa"] == ccaa and (provincia is None or r["provincia"] == provincia)]
    mejor, pmejor = None, 0.0
    for r in cand:
        for v in variantes(r["NOMBRE"]):
            p = difflib.SequenceMatcher(None, n, _ART.sub("", v)).ratio()
            if p > pmejor:
                mejor, pmejor = r, p
    return mejor if pmejor >= umbral else None


_orig_prefijo = buscar_prefijo


def buscar_prefijo(nombre: str, ccaa: str, provincia: str) -> dict | None:  # noqa: F811
    r = _orig_prefijo(nombre, ccaa, provincia)
    if r:
        return r
    limpio = re.sub(r"\s*\((el|la|los|las|l')\)\s*", " ", nombre, flags=re.I).strip()
    limpio = _ART.sub("", norm(limpio))
    cand = [x for x in REG if x["ccaa"] == ccaa and x["provincia"] == provincia
            and _ART.sub("", primaria(x["NOMBRE"])).startswith(limpio + " ")]
    return cand[0] if len(cand) == 1 else None


# Nombres de uso habitual en los boletines que no casan solos con el INE.
ALIAS_MANUAL = {
    "Castell-Platja d'Aro": "Castell d'Aro, Platja d'Aro i s'Agaró",
    "Cruïlles": "Cruïlles, Monells i Sant Sadurní de l'Heura",
    "Rúa de Valdeorras, A": "Rúa, A",
    "PLACENCIA DE LAS ARMAS": "Soraluze-Placencia de las Armas",
    "RAFÓL DE ALMÚNIA": "Ràfol d'Almúnia, El",
    "Bejíjar": "Begíjar",
    "Peñas de Riglos (Las) (Riglos)": "Peñas de Riglos, Las",
    "Veracruz (Beranuy)": "Beranuy",
    "Nalón": "Muros de Nalón",
    "San Bartolomé de Lanzarote": "San Bartolomé",
    "Santa Lucía": "Santa Lucía de Tirajana",
    "Santa María de Guía": "Santa María de Guía de Gran Canaria",
    "Valsequillo": "Valsequillo de Gran Canaria",
    "Hdad. Campoo de Suso": "Hermandad de Campoo de Suso",
    "LA POBLA DE TORNESA": "Pobla Tornesa, la",
}
_orig_buscar = buscar


def buscar(nombre: str, ccaa: str, provincia: str | None = None) -> dict | None:  # noqa: F811
    if nombre in ALIAS_MANUAL:
        nombre = ALIAS_MANUAL[nombre]
    return _orig_buscar(nombre, ccaa, provincia)
