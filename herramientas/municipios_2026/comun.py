"""Utilidades comunes para extraer fiestas locales de los boletines."""
import json, re, unicodedata
from datetime import date
from pathlib import Path

# Boletines descargados (PDF/HTML) y su texto extraído con txt.py; no se suben al repositorio.
LOC = Path(__file__).resolve().parent / "boletines"
OUT = Path(__file__).resolve().parent / "salida"
OUT.mkdir(exist_ok=True)

MESES = {
    # castellano
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
    "septiembre": 9, "setiembre": 9, "sptiembre": 9, "septembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    # catalán / valenciano / balear
    "gener": 1, "febrer": 2, "març": 3, "abril": 4, "maig": 5, "juny": 6, "juliol": 7, "agost": 8,
    "setembre": 9, "octubre": 10, "novembre": 11, "desembre": 12,
    # gallego
    "xaneiro": 1, "febreiro": 2, "marzo": 3, "abril": 4, "maio": 5, "xuño": 6, "xullo": 7, "agosto": 8,
    "setembro": 9, "outubro": 10, "novembro": 11, "decembro": 12,
    # euskera (forma usada en los boletines: "Urtarrilak 20")
    "urtarrilak": 1, "otsailak": 2, "martxoak": 3, "apirilak": 4, "maiatzak": 5, "ekainak": 6,
    "uztailak": 7, "abuztuak": 8, "irailak": 9, "urriak": 10, "azaroak": 11, "abenduak": 12,
}
_M = "|".join(sorted(MESES, key=len, reverse=True))
# Una fecha seguida de un año que no es 2026 (cabeceras «26 de septiembre de 2025») no cuenta.
OTRO_ANIO = r"(?!\s*,?\s*(?:de\s*)?20(?!26)\d\d)"
RE_FECHA = re.compile(rf"\b(\d{{1,2}})\s*(?:de\s*|d'|d’)?\s*({_M})\b{OTRO_ANIO}", re.I)
RE_FECHA_NUM = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](2026)\b")


def fechas(texto: str) -> list[str]:
    """Todas las fechas (2026) de un texto, en orden y sin repetir. Admite «10 y 11 de septiembre»."""
    out = []
    t = texto.replace("\u00a0", " ")
    # «17 de agosto (por traslado del día 16 de agosto)»: solo cuenta el día al que se traslada.
    t = re.sub(rf"\(?\s*por traslado del?\s*(?:día\s*)?\d{{1,2}}\s*(?:de\s*)?(?:{_M})\s*\)?", " ", t, flags=re.I)
    # «17 de enero, San Antonio Abad, se traslada al 16 de enero»: cuenta el 16.
    t = re.sub(rf"\d{{1,2}}\s*(?:de\s*)?(?:{_M})([^0-9]{{0,80}}?)se traslada\s+(?:al?|para el)\s*(?:día\s*)?",
               r"\1 ", t, flags=re.I)
    # «7 y 8 de septiembre», «27, 28 y 29 de agosto»
    for m in re.finditer(rf"((?:\d{{1,2}}\s*(?:,|y|i|e)\s*)+)(\d{{1,2}})\s*(?:de\s*|d'|d’)?\s*({_M})\b{OTRO_ANIO}", t, re.I):
        mes = MESES[m.group(3).lower()]
        for d in re.findall(r"\d{1,2}", m.group(1)):
            out.append((m.start(), date(2026, mes, int(d)).isoformat()))
    for m in RE_FECHA.finditer(t):
        out.append((m.start(), date(2026, MESES[m.group(2).lower()], int(m.group(1))).isoformat()))
    for m in RE_FECHA_NUM.finditer(t):
        out.append((m.start(), date(2026, int(m.group(2)), int(m.group(1))).isoformat()))
    vistos, res = set(), []
    for _, f in sorted(out):
        if f not in vistos:
            vistos.add(f); res.append(f)
    return res


def nombre(n: str) -> str:
    """«BOSQUE, EL» -> «El Bosque»; espacios y mayúsculas normalizados."""
    n = " ".join(n.replace("\u00a0", " ").split()).strip(" .:-–—,")
    m = re.fullmatch(r"(.+?),\s*(el|la|los|las|l'|l’|els|les|o|a|os|as|lo|sa|ses|es|s')", n, re.I)
    if m:
        art = m.group(2)
        n = f"{art}{'' if art.endswith(('’', chr(39))) else ' '}{m.group(1)}"
    if n.isupper() or n.islower():
        palabras = []
        for i, p in enumerate(n.lower().split(" ")):
            if i and p in {"de", "del", "la", "las", "los", "el", "y", "i", "e", "d'", "da", "do", "dos", "das", "en", "des", "sa", "ses", "es", "dels", "al", "a", "o", "na", "da"}:
                palabras.append(p)
            else:
                palabras.append("-".join(x[:1].upper() + x[1:] for x in p.split("-")))
        n = " ".join(palabras)
        n = re.sub(r"\b([DL])'(\w)", lambda m: m.group(1) + "'" + m.group(2).upper(), n)
    return n


def clave(n: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", n) if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9ñ' ]", " ", s.lower().replace("’", "'")).split())


def guardar(ccaa: str, registros: list[dict], fuente: str) -> None:
    for r in registros:
        r.setdefault("ccaa", ccaa)
        r["fuente"] = fuente
    (OUT / f"{ccaa}.json").write_text(json.dumps(registros, ensure_ascii=False, indent=0), encoding="utf-8")
    sin = [r["nombre"] for r in registros if not r["dias"]]
    mas = [(r["nombre"], r["dias"]) for r in registros if len(r["dias"]) > 2]
    provs = {}
    for r in registros:
        provs[r.get("provincia")] = provs.get(r.get("provincia"), 0) + 1
    print(f"{ccaa}: {len(registros)} municipios {provs} | sin fecha: {len(sin)} {sin[:8]} | >2 fechas: {len(mas)} {mas[:5]}")


def lineas(fichero: str) -> list[str]:
    return [l.strip() for l in (LOC / fichero).read_text(encoding="utf-8").splitlines()]
