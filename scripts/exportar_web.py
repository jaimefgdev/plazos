"""Genera web/datos.js con los calendarios que usa la herramienta web.

    python scripts/exportar_web.py

Los motivos de cada festivo salen de plazos.Calendario, así la web no repite la lógica
de BOE, librería holidays y fiestas locales: solo aplica las reglas de cómputo.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from plazos import __version__  # noqa: E402
from plazos import normas as N  # noqa: E402
from plazos.calendario import CCAA, LOCALES, OFICIALES, Calendario, Lugar  # noqa: E402
from plazos.datos import boe_2026  # noqa: E402

ANIOS = range(2024, 2032)


def dias(anio: int):
    d = date(anio, 1, 1)
    while d.year == anio:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def main() -> None:
    festivos: dict[str, dict[str, dict[str, str]]] = {}
    for anio in ANIOS:
        nacional = Calendario([Lugar()])
        por_ccaa: dict[str, dict[str, str]] = {"ES": {}}
        for d in dias(anio):
            motivo = nacional.festivo(d)
            if motivo:
                por_ccaa["ES"][d.isoformat()] = motivo
        for cc in CCAA:
            cal = Calendario([Lugar(cc)])
            propios = {}
            for d in dias(anio):
                motivo = cal.festivo(d)
                if motivo and d.isoformat() not in por_ccaa["ES"]:
                    propios[d.isoformat()] = motivo
            por_ccaa[cc] = propios
        festivos[str(anio)] = por_ccaa

    capitales = {}
    fuentes = {}
    for anio, datos in LOCALES.items():
        capitales[str(anio)] = [
            {"nombre": n, "ccaa": cc, "isla": isla, "dias": [date(anio, m, d).isoformat() for m, d in ds]}
            for n, cc, isla, ds in datos.CAPITALES.values()
        ]
        fuentes[str(anio)] = {cc: {"texto": t, "url": u} for cc, (t, u) in datos.FUENTES.items()}

    insulares = {
        str(anio): {isla: date(anio, m, d).isoformat() for isla, (m, d) in datos.INSULARES_CANARIAS.items()}
        for anio, datos in OFICIALES.items()
    }
    normas = {nombre: {"cita": n.cita, "url": n.url} for nombre, n in vars(N).items() if isinstance(n, N.Norma)}

    datos = {
        "version": __version__,
        "ccaa": CCAA,
        "oficiales": sorted(OFICIALES),
        "boe": {"referencia": boe_2026.REFERENCIA, "url": boe_2026.URL},
        "festivos": festivos,
        "insulares": insulares,
        "capitales": capitales,
        "fuentes": fuentes,
        "normas": normas,
    }
    destino = RAIZ / "web" / "datos.js"
    destino.write_text(
        "// Generado por scripts/exportar_web.py: no editar a mano.\n"
        "globalThis.PLAZOS_DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{destino.relative_to(RAIZ)}: {destino.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
