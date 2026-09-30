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

import holidays  # noqa: E402

from plazos import __version__, municipios  # noqa: E402
from plazos import normas as N  # noqa: E402
from plazos.calendario import CCAA, OFICIALES, Calendario, Lugar  # noqa: E402
from plazos.datos import boe_2026  # noqa: E402

ANIOS = range(2024, 2032)


def dias(anio: int):
    d = date(anio, 1, 1)
    while d.year == anio:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def main(destino: Path | None = None) -> None:
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

    # Fiestas locales de todos los municipios: fichero aparte que la web carga al empezar.
    fuentes: dict[str, dict[str, str]] = {}
    lista = []
    for anio in municipios.ANIOS:
        for m in sorted(municipios.todos(anio), key=lambda m: m.ine):
            clave = fuentes.setdefault(m.fuente, {"texto": m.fuente, "url": m.url, "id": str(len(fuentes))})["id"]
            lista.append(
                [
                    m.ine,
                    m.nombre_legible,
                    m.ccaa,
                    m.provincia,
                    m.isla or "",
                    [d.isoformat() for d in m.dias],
                    [[p.fecha.isoformat(), p.ambito] for p in m.parciales],
                    int(clave),
                    anio,
                ]
            )
    mun = {"fuentes": [{"texto": f["texto"], "url": f["url"]} for f in fuentes.values()], "municipios": lista}
    ruta_mun = (destino or RAIZ / "web" / "datos.js").with_name("municipios.json")
    ruta_mun.write_text(json.dumps(mun, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")

    insulares = {
        str(anio): {isla: date(anio, m, d).isoformat() for isla, (m, d) in datos.INSULARES_CANARIAS.items()}
        for anio, datos in OFICIALES.items()
    }
    normas = {nombre: {"cita": n.cita, "url": n.url} for nombre, n in vars(N).items() if isinstance(n, N.Norma)}

    datos = {
        "version": __version__,
        "holidays": holidays.__version__,
        "ccaa": CCAA,
        "oficiales": sorted(OFICIALES),
        "boe": {"referencia": boe_2026.REFERENCIA, "url": boe_2026.URL},
        "festivos": festivos,
        "insulares": insulares,
        "aniosMunicipios": list(municipios.ANIOS),
        "normas": normas,
    }
    destino = destino or RAIZ / "web" / "datos.js"
    destino.write_text(
        "// Generado por scripts/exportar_web.py: no editar a mano.\n"
        "globalThis.PLAZOS_DATOS = " + json.dumps(datos, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{destino.name}: {destino.stat().st_size // 1024} KB; municipios.json: {ruta_mun.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
