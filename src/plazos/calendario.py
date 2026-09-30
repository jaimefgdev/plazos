"""Festivos nacionales, autonómicos y locales que hacen inhábil un día."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from functools import cache

import holidays

from .datos import boe_2026, locales_2026

CCAA = {
    "AN": "Andalucía",
    "AR": "Aragón",
    "AS": "Principado de Asturias",
    "IB": "Illes Balears",
    "CN": "Canarias",
    "CB": "Cantabria",
    "CL": "Castilla y León",
    "CM": "Castilla-La Mancha",
    "CT": "Cataluña",
    "EX": "Extremadura",
    "GA": "Galicia",
    "MD": "Comunidad de Madrid",
    "MC": "Región de Murcia",
    "NC": "Comunidad Foral de Navarra",
    "PV": "País Vasco",
    "RI": "La Rioja",
    "VC": "Comunitat Valenciana",
    "CE": "Ciudad de Ceuta",
    "ML": "Ciudad de Melilla",
}

# Años cuyo calendario nacional y autonómico viene del BOE, no de la librería holidays.
OFICIALES = {2026: boe_2026}
# Años con fiestas locales de las capitales de provincia sacadas de los boletines oficiales.
LOCALES = {2026: locales_2026}


def _normalizar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return " ".join(sin_tildes.lower().replace("’", "'").split())


def capital(nombre: str) -> tuple[str, str, str | None] | None:
    """(nombre oficial, comunidad, isla) si ``nombre`` es una capital con datos, o ``None``."""
    clave = _normalizar(nombre)
    for datos in LOCALES.values():
        clave = datos.ALIAS.get(clave, clave)
        if clave in datos.CAPITALES:
            oficial, ccaa, isla, _ = datos.CAPITALES[clave]
            return oficial, ccaa, isla
    return None


def fiestas_locales(nombre: str, anio: int) -> tuple[date, ...] | None:
    """Fiestas locales oficiales de una capital en ``anio``, o ``None`` si no hay datos."""
    datos = LOCALES.get(anio)
    if datos is None:
        return None
    clave = _normalizar(nombre)
    clave = datos.ALIAS.get(clave, clave)
    if clave not in datos.CAPITALES:
        return None
    return tuple(date(anio, m, d) for m, d in datos.CAPITALES[clave][3])


def fuente_locales(ccaa: str, anio: int) -> tuple[str, str] | None:
    datos = LOCALES.get(anio)
    return datos.FUENTES.get(ccaa) if datos else None


@dataclass(frozen=True)
class Lugar:
    """Territorio cuyos festivos cuentan: comunidad, isla (Canarias) y días locales."""

    ccaa: str | None = None
    festivos_locales: tuple[date, ...] = field(default=())
    isla: str | None = None
    municipio: str | None = None

    def __post_init__(self) -> None:
        conocida = capital(self.municipio) if self.municipio else None
        if conocida:
            oficial, ccaa, isla = conocida
            if self.ccaa is not None and self.ccaa != ccaa:
                raise ValueError(f"{oficial} está en {CCAA[ccaa]} ({ccaa}), no en {self.ccaa}")
            object.__setattr__(self, "municipio", oficial)
            object.__setattr__(self, "ccaa", ccaa)
            if self.isla is None:
                object.__setattr__(self, "isla", isla)
        if self.ccaa is not None and self.ccaa not in CCAA:
            raise ValueError(f"Comunidad desconocida: {self.ccaa!r}. Usa uno de: {', '.join(CCAA)}")
        if self.isla is not None:
            if self.ccaa != "CN":
                raise ValueError("La isla solo se indica para Canarias (ccaa='CN')")
            if self.isla not in boe_2026.INSULARES_CANARIAS:
                raise ValueError(f"Isla desconocida: {self.isla!r}")
        object.__setattr__(self, "festivos_locales", tuple(sorted(set(self.festivos_locales))))


@cache
def _nombres(anio: int, ccaa: str | None) -> dict[date, str]:
    return dict(holidays.country_holidays("ES", years=anio, subdiv=ccaa))


def _nombre(d: date, ccaa: str | None) -> str | None:
    return _nombres(d.year, ccaa).get(d)


class Calendario:
    """Une los festivos de uno o varios lugares.

    Con varios lugares, un día festivo en cualquiera de ellos es inhábil
    (Ley 39/2015, art. 30.6: domicilio del interesado y sede del órgano).
    """

    def __init__(self, lugares: Iterable[Lugar] = ()) -> None:
        self.lugares = tuple(lugares) or (Lugar(),)

    @staticmethod
    def es_oficial(anio: int) -> bool:
        return anio in OFICIALES

    def locales_conocidos(self, anio: int) -> bool:
        """Si todos los lugares tienen sus fiestas locales de ``anio`` (dadas o incluidas)."""
        return all(
            (lugar.festivos_locales and any(d.year == anio for d in lugar.festivos_locales))
            or (lugar.municipio and fiestas_locales(lugar.municipio, anio) is not None)
            for lugar in self.lugares
        )

    def festivo(self, d: date) -> str | None:
        """Motivo por el que ``d`` es festivo, o ``None`` si no lo es en ningún lugar."""
        motivos: list[str] = []
        for lugar in self.lugares:
            for motivo in self._motivos(d, lugar):
                if motivo not in motivos:
                    motivos.append(motivo)
        return "; ".join(motivos) or None

    def _motivos(self, d: date, lugar: Lugar) -> list[str]:
        motivos = []
        nacional, autonomico = self._oficial(d, lugar.ccaa)
        if nacional:
            nombre = _nombre(d, None)
            motivos.append("festivo nacional" + (f" ({nombre})" if nombre else ""))
        elif autonomico and lugar.ccaa:
            nombre = _nombre(d, lugar.ccaa)
            motivos.append(f"festivo en {CCAA[lugar.ccaa]}" + (f" ({nombre})" if nombre else ""))
        if (
            lugar.isla
            and self.es_oficial(d.year)
            and OFICIALES[d.year].INSULARES_CANARIAS[lugar.isla] == (d.month, d.day)
        ):
            motivos.append(f"festivo insular en {lugar.isla}")
        oficiales = fiestas_locales(lugar.municipio, d.year) if lugar.municipio else None
        if d in lugar.festivos_locales or (oficiales and d in oficiales):
            motivos.append("festivo local" + (f" en {lugar.municipio}" if lugar.municipio else ""))
        return motivos

    def _oficial(self, d: date, ccaa: str | None) -> tuple[bool, bool]:
        """(es festivo nacional, es festivo en la comunidad)."""
        datos = OFICIALES.get(d.year)
        if datos is not None:
            ambito = datos.DIAS.get((d.month, d.day))
            if ambito is None:
                return False, False
            if ambito == "ES":
                return True, False
            return False, ccaa in ambito
        # Sin calendario del BOE incorporado: se usa la librería holidays.
        if d in _nombres(d.year, None):
            return True, False
        return False, ccaa is not None and d in _nombres(d.year, ccaa)
