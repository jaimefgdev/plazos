"""Línea de órdenes: ``plazos 2026-07-20 10 dias --ccaa MD``."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from . import __version__
from .calendario import CCAA
from .computo import JURISDICCIONES, UNIDADES, calcular


def _fecha(texto: str) -> date:
    try:
        return date.fromisoformat(texto)
    except ValueError:
        raise argparse.ArgumentTypeError(f"fecha no válida: {texto!r} (formato AAAA-MM-DD)") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="plazos",
        description="Calcula el vencimiento de un plazo administrativo o judicial español y explica cada paso.",
        epilog="Ejemplo: plazos 2026-07-20 20 dias -j civil --ccaa MD --local 2026-05-15 --local 2026-11-09",
    )
    parser.add_argument("inicio", type=_fecha, help="día de la notificación o publicación (AAAA-MM-DD)")
    parser.add_argument("cantidad", type=int, help="duración del plazo")
    parser.add_argument("unidad", nargs="?", default="dias", choices=UNIDADES, help="por defecto, dias (hábiles)")
    parser.add_argument("-j", "--jurisdiccion", default="administrativo", choices=JURISDICCIONES)
    parser.add_argument("--ccaa", choices=sorted(CCAA), help="comunidad autónoma (código ISO)")
    parser.add_argument(
        "--local", action="append", type=_fecha, default=[], metavar="FECHA", help="festivo local; repetible"
    )
    parser.add_argument(
        "--municipio", help="municipio; en las 50 capitales de provincia se añaden solos sus festivos locales"
    )
    parser.add_argument("--isla", help="isla, para los festivos insulares de Canarias")
    parser.add_argument(
        "--urgente", action="store_true", help="actuación urgente: agosto y del 24-12 al 6-1 son hábiles"
    )
    parser.add_argument("--json", action="store_true", help="salida en JSON")
    parser.add_argument("-V", "--version", action="version", version=f"plazos {__version__}")
    args = parser.parse_args(argv)

    try:
        r = calcular(
            args.inicio,
            args.cantidad,
            args.unidad,
            args.jurisdiccion,
            ccaa=args.ccaa,
            festivos_locales=args.local,
            municipio=args.municipio,
            isla=args.isla,
            urgente=args.urgente,
        )
    except ValueError as e:
        parser.error(str(e))
    if args.json:
        json.dump(
            {
                "vencimiento": r.vencimiento.isoformat(),
                "presentacion_hasta": r.presentacion_hasta.isoformat() if r.presentacion_hasta else None,
                "pasos": [{"texto": p.texto, "norma": p.norma.cita if p.norma else None} for p in r.pasos],
                "excluidos": [{"fecha": e.fecha.isoformat(), "motivo": e.motivo} for e in r.excluidos],
                "advertencias": list(r.advertencias),
                "normas": [{"cita": n.cita, "url": n.url} for n in r.normas],
            },
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        print()
    else:
        print(r.explicar())
        print("\nOrientativo: comprueba siempre el calendario oficial y la norma aplicable a tu caso.")
    return 0
