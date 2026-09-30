"""Fiestas locales de los municipios, sacadas de los boletines oficiales de cada comunidad.

Cada año hay un fichero ``datos/municipios_AAAA.json`` con, por municipio: código INE,
comunidad, provincia, sus fiestas locales (``dias``), las que solo rigen en parte del
término (``parciales``: pedanías, parroquias, entidades locales menores) y la fuente.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from functools import cache
from importlib import resources

from .datos import locales_2026

ANIOS = (2026,)


@dataclass(frozen=True)
class Parcial:
    fecha: date
    ambito: str


@dataclass(frozen=True)
class Municipio:
    ine: str
    nombre: str
    ccaa: str
    provincia: str
    dias: tuple[date, ...]
    parciales: tuple[Parcial, ...]
    fuente: str
    url: str
    isla: str | None = None

    @property
    def nombre_legible(self) -> str:
        return legible(self.nombre)


def normalizar(texto: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[^a-z0-9ñç' ]+", " ", s.replace("’", "'").replace("´", "'"))
    return " ".join(s.split())


_ART = re.compile(r"^(el|la|los|las|l'|els|les|o|a|os|as|lo|sa|ses|es|s')\s*")


def legible(nombre: str) -> str:
    """«Palmas de Gran Canaria, Las» -> «Las Palmas de Gran Canaria» (también en nombres bilingües)."""

    def uno(p: str) -> str:
        m = re.fullmatch(r"(.+?),\s*(el|la|los|las|l'|els|les|o|a|os|as|lo|sa|ses|es|s')", p.strip(), re.I)
        if not m:
            return p.strip()
        art = m.group(2)
        art = art[:1].upper() + art[1:]
        return f"{art}{'' if art.endswith(chr(39)) else ' '}{m.group(1)}"

    return "/".join(uno(p) for p in nombre.split("/"))


def _variantes(nombre: str) -> set[str]:
    out: set[str] = set()
    for parte in [nombre, *nombre.split("/")]:
        for forma in (parte, legible(parte)):
            n = normalizar(forma)
            out |= {n, _ART.sub("", n), n.replace("'", "")}
    return {v for v in out if v}


@cache
def _cargar(anio: int) -> tuple[dict[str, Municipio], dict[str, list[Municipio]]]:
    ruta = resources.files("plazos.datos").joinpath(f"municipios_{anio}.json")
    crudo = json.loads(ruta.read_text(encoding="utf-8"))
    fuentes = crudo["fuentes"]
    por_ine: dict[str, Municipio] = {}
    indice: dict[str, list[Municipio]] = {}
    for r in crudo["municipios"]:
        f = fuentes[r["fuente"]]
        m = Municipio(
            ine=r["ine"],
            nombre=r["nombre"],
            ccaa=r["ccaa"],
            provincia=r["provincia"],
            dias=tuple(date.fromisoformat(d) for d in r["dias"]),
            parciales=tuple(Parcial(date.fromisoformat(p["fecha"]), p["ambito"]) for p in r["parciales"]),
            fuente=f["texto"],
            url=f["url"],
            isla=r.get("isla"),
        )
        por_ine[m.ine] = m
        for v in _variantes(m.nombre):
            indice.setdefault(v, []).append(m)
    return por_ine, indice


def buscar(nombre: str, anio: int = 2026, ccaa: str | None = None, provincia: str | None = None) -> Municipio | None:
    """Municipio por nombre (con o sin tildes y artículo) o por código INE de cinco cifras.

    Devuelve ``None`` si no hay datos de ese municipio para ``anio``. Si el nombre es de
    varios municipios y ``ccaa``/``provincia`` no bastan para distinguirlos, lanza ValueError.
    """
    if anio not in ANIOS:
        return None
    por_ine, indice = _cargar(anio)
    if re.fullmatch(r"\d{5}", nombre.strip()):
        return por_ine.get(nombre.strip())
    clave = normalizar(nombre)
    candidatos = indice.get(clave) or indice.get(_ART.sub("", clave), [])
    if not candidatos and clave in locales_2026.ALIAS:  # «Palma de Mallorca», «La Coruña», «Gerona»…
        clave = normalizar(locales_2026.CAPITALES[locales_2026.ALIAS[clave]][0])
        candidatos = indice.get(clave, [])
    if not candidatos:
        # «Las Palmas» -> «Las Palmas de Gran Canaria», «Vitoria» -> «Vitoria-Gasteiz»: prefijo único.
        candidatos = list({m.ine: m for v, ms in indice.items() if v.startswith(clave + " ") for m in ms}.values())
    if ccaa:
        candidatos = [m for m in candidatos if m.ccaa == ccaa]
    if provincia:
        p = normalizar(provincia)
        candidatos = [m for m in candidatos if p in normalizar(m.provincia)]
    unicos = list({m.ine: m for m in candidatos}.values())
    if len(unicos) > 1:
        # Si hay una coincidencia exacta de nombre, se prefiere a las de prefijo.
        exactos = [m for m in unicos if clave in _variantes(m.nombre)]
        if len(exactos) == 1:
            return exactos[0]
        opciones = "; ".join(f"{legible(m.nombre)} ({m.provincia}, INE {m.ine})" for m in unicos[:8])
        raise ValueError(f"Hay varios municipios llamados «{nombre}»: {opciones}. Indica la provincia o el código INE.")
    return unicos[0] if unicos else None


def todos(anio: int = 2026) -> list[Municipio]:
    return list(_cargar(anio)[0].values()) if anio in ANIOS else []
