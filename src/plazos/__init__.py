"""Cálculo de plazos administrativos y procesales españoles, con la explicación y la norma de cada paso."""

from .calendario import CCAA, Calendario, Lugar
from .computo import JURISDICCIONES, UNIDADES, DiaExcluido, Paso, Resultado, calcular, fecha_larga, plazo_pago

__all__ = [
    "CCAA",
    "JURISDICCIONES",
    "UNIDADES",
    "Calendario",
    "DiaExcluido",
    "Lugar",
    "Paso",
    "Resultado",
    "calcular",
    "fecha_larga",
    "plazo_pago",
]
__version__ = "0.3.0"
