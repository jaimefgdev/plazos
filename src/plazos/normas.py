"""Citas legales que usa el motor, con enlace al texto consolidado del BOE."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Norma:
    cita: str
    url: str

    def __str__(self) -> str:
        return self.cita


def _boe(id_boe: str, bloque: str) -> str:
    return f"https://www.boe.es/buscar/act.php?id={id_boe}#{bloque}"


L39 = "BOE-A-2015-10565"
LEC = "BOE-A-2000-323"
LOPJ = "BOE-A-1985-12666"
LJCA = "BOE-A-1998-16718"
LRJS = "BOE-A-2011-15936"
LGT = "BOE-A-2003-23186"

L39_30_1 = Norma("Ley 39/2015, art. 30.1", _boe(L39, "a30"))
L39_30_2 = Norma("Ley 39/2015, art. 30.2", _boe(L39, "a30"))
L39_30_3 = Norma("Ley 39/2015, art. 30.3", _boe(L39, "a30"))
L39_30_4 = Norma("Ley 39/2015, art. 30.4", _boe(L39, "a30"))
L39_30_5 = Norma("Ley 39/2015, art. 30.5", _boe(L39, "a30"))
L39_30_6 = Norma("Ley 39/2015, art. 30.6", _boe(L39, "a30"))
L39_31_2 = Norma("Ley 39/2015, art. 31.2", _boe(L39, "a31"))

LEC_130_2 = Norma("LEC, art. 130.2", _boe(LEC, "a130"))
LEC_133_1 = Norma("LEC, art. 133.1", _boe(LEC, "a133"))
LEC_133_2 = Norma("LEC, art. 133.2", _boe(LEC, "a133"))
LEC_133_3 = Norma("LEC, art. 133.3", _boe(LEC, "a133"))
LEC_133_4 = Norma("LEC, art. 133.4", _boe(LEC, "a133"))
LEC_135_5 = Norma("LEC, art. 135.5", _boe(LEC, "a135"))

LOPJ_182 = Norma("LOPJ, art. 182", _boe(LOPJ, "acientoochentaydos"))
LOPJ_183 = Norma("LOPJ, art. 183", _boe(LOPJ, "acientoochentaytres"))
LOPJ_185 = Norma("LOPJ, art. 185", _boe(LOPJ, "acientoochentaycinco"))

LJCA_46_1 = Norma("LJCA, art. 46.1", _boe(LJCA, "a46"))
LJCA_128_2 = Norma("LJCA, art. 128.2", _boe(LJCA, "a128"))

LRJS_43_4 = Norma("LRJS, art. 43.4", _boe(LRJS, "a43"))
LRJS_45_1 = Norma("LRJS, art. 45.1", _boe(LRJS, "a45"))

LGT_7_2 = Norma("LGT, art. 7.2", _boe(LGT, "a7"))
LGT_62_2 = Norma("LGT, art. 62.2", _boe(LGT, "a62"))
LGT_62_5 = Norma("LGT, art. 62.5", _boe(LGT, "a62"))
