"""Cómputo de plazos administrativos y procesales."""

from __future__ import annotations

import calendar
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from . import normas as N
from .calendario import CCAA, Calendario, Lugar, fiestas_locales, fuente_locales

JURISDICCIONES = ("administrativo", "civil", "contencioso", "social")
UNIDADES = ("dias", "dias_naturales", "meses", "anios")
_JUDICIALES = ("civil", "contencioso", "social")
_DIAS_SEMANA = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
_MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def fecha_larga(d: date) -> str:
    """``martes, 4 de agosto de 2026``."""
    return f"{_DIAS_SEMANA[d.weekday()]}, {d.day} de {_MESES[d.month - 1]} de {d.year}"


@dataclass(frozen=True)
class Paso:
    texto: str
    norma: N.Norma | None = None

    def __str__(self) -> str:
        return f"{self.texto} ({self.norma})" if self.norma else self.texto


@dataclass(frozen=True)
class DiaExcluido:
    fecha: date
    motivo: str


@dataclass(frozen=True)
class Resultado:
    inicio: date
    cantidad: int
    unidad: str
    jurisdiccion: str
    vencimiento: date
    pasos: tuple[Paso, ...]
    excluidos: tuple[DiaExcluido, ...] = ()
    advertencias: tuple[str, ...] = ()
    presentacion_hasta: datetime | None = None
    normas: tuple[N.Norma, ...] = field(default=())

    def explicar(self) -> str:
        lineas = [f"Vence el {fecha_larga(self.vencimiento)}."]
        if self.presentacion_hasta:
            lineas.append(
                "Último momento para presentar: "
                f"{fecha_larga(self.presentacion_hasta.date())} a las "
                f"{self.presentacion_hasta:%H:%M}."
            )
        lineas.append("")
        lineas += [f"{i}. {p}" for i, p in enumerate(self.pasos, 1)]
        if self.advertencias:
            lineas.append("")
            lineas += [f"Aviso: {a}" for a in self.advertencias]
        return "\n".join(lineas)


class _Reglas:
    """Qué días son inhábiles según la jurisdicción."""

    def __init__(self, jurisdiccion: str, cal: Calendario, urgente: bool) -> None:
        self.jurisdiccion = jurisdiccion
        self.cal = cal
        self.urgente = urgente
        self.judicial = jurisdiccion in _JUDICIALES

    def inhabil(self, d: date) -> str | None:
        if d.weekday() == 5:
            return "sábado"
        if d.weekday() == 6:
            return "domingo"
        festivo = self.cal.festivo(d)
        if festivo:
            return festivo
        if self.judicial and not self.urgente:
            if d.month == 8:
                return "agosto, inhábil en los juzgados"
            if (d.month, d.day) >= (12, 24) or (d.month, d.day) <= (1, 6):
                return "del 24 de diciembre al 6 de enero, inhábil en los juzgados"
        return None

    def siguiente_habil(self, d: date) -> tuple[date, list[DiaExcluido]]:
        saltados = []
        while motivo := self.inhabil(d):
            saltados.append(DiaExcluido(d, motivo))
            d += timedelta(days=1)
        return d, saltados


def _sumar_meses(d: date, meses: int) -> date:
    total = d.month - 1 + meses
    anio, mes = d.year + total // 12, total % 12 + 1
    return date(anio, mes, min(d.day, calendar.monthrange(anio, mes)[1]))


def _norma_dias(jurisdiccion: str) -> N.Norma:
    return {"administrativo": N.L39_30_2, "social": N.LOPJ_185}.get(jurisdiccion, N.LEC_133_2)


def _norma_inhabiles(jurisdiccion: str) -> N.Norma:
    return {"administrativo": N.L39_30_2, "social": N.LRJS_43_4}.get(jurisdiccion, N.LEC_130_2)


def _resumen_excluidos(excluidos: Sequence[DiaExcluido]) -> str:
    """Agrupa los días excluidos por motivo, sin listar cada fin de semana."""
    finde = sum(1 for e in excluidos if e.motivo in ("sábado", "domingo"))
    otros = [e for e in excluidos if e.motivo not in ("sábado", "domingo")]
    partes = []
    if finde:
        partes.append(f"{finde} {'día' if finde == 1 else 'días'} de fin de semana")
    agrupados: dict[str, list[date]] = {}
    for e in otros:
        agrupados.setdefault(e.motivo, []).append(e.fecha)
    for motivo, fechas in agrupados.items():
        if len(fechas) > 3:
            partes.append(f"{len(fechas)} días ({fechas[0]:%d/%m} a {fechas[-1]:%d/%m}): {motivo}")
        else:
            partes.append(", ".join(f"{f:%d/%m/%Y}" for f in fechas) + f": {motivo}")
    return "; ".join(partes)


def calcular(
    inicio: date,
    cantidad: int,
    unidad: str = "dias",
    jurisdiccion: str = "administrativo",
    *,
    ccaa: str | None = None,
    festivos_locales: Iterable[date] = (),
    municipio: str | None = None,
    isla: str | None = None,
    lugares: Iterable[Lugar] = (),
    urgente: bool = False,
) -> Resultado:
    """Calcula el vencimiento de un plazo.

    ``inicio`` es el día de la notificación o publicación: el cómputo empieza al día
    siguiente. ``ccaa``, ``festivos_locales``, ``municipio`` e ``isla`` describen un
    lugar; para varios (p. ej. domicilio del interesado y sede del órgano), usa
    ``lugares``. ``urgente`` marca las actuaciones en las que agosto y el periodo del
    24 de diciembre al 6 de enero son hábiles (LEC 131.2, LRJS 43.4, derechos
    fundamentales en la LJCA 128.2).
    """
    if jurisdiccion not in JURISDICCIONES:
        raise ValueError(f"Jurisdicción desconocida: {jurisdiccion!r}. Usa: {', '.join(JURISDICCIONES)}")
    if unidad not in UNIDADES:
        raise ValueError(f"Unidad desconocida: {unidad!r}. Usa: {', '.join(UNIDADES)}")
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 1:
        raise ValueError("La cantidad debe ser un número entero positivo")
    if unidad == "dias_naturales" and jurisdiccion != "administrativo":
        raise ValueError("Los plazos procesales se cuentan en días hábiles, no naturales")
    if urgente and jurisdiccion == "administrativo":
        raise ValueError("'urgente' solo se aplica a plazos judiciales")

    lista = list(lugares)
    if ccaa or festivos_locales or municipio or isla:
        lista.insert(0, Lugar(ccaa, tuple(festivos_locales), isla, municipio))
    cal = Calendario(lista)
    reglas = _Reglas(jurisdiccion, cal, urgente)
    pasos: list[Paso] = []
    avisos: list[str] = []
    excluidos: list[DiaExcluido] = []
    normas: list[N.Norma] = []

    def paso(texto: str, norma: N.Norma | None = None) -> None:
        pasos.append(Paso(texto, norma))
        if norma and norma not in normas:
            normas.append(norma)

    # 1) Norma y calendario aplicables.
    if jurisdiccion == "administrativo":
        paso("Plazo administrativo: se aplica la Ley 39/2015 de Procedimiento Administrativo Común", N.L39_30_2)
    else:
        nombre = {
            "civil": "civil (LEC)",
            "contencioso": "contencioso-administrativo (LJCA; LEC supletoria)",
            "social": "social (LRJS)",
        }[jurisdiccion]
        paso(f"Plazo procesal del orden {nombre}; los días inhábiles judiciales los fija la LOPJ", N.LOPJ_182)
        if urgente:
            texto = {
                "social": "Modalidad procesal urgente: agosto y del 24 de diciembre al 6 de enero son hábiles",
                "contencioso": "Procedimiento de derechos fundamentales: agosto es hábil",
                "civil": "Actuación urgente: agosto es hábil y solo se excluyen sábados, domingos y festivos",
            }
            paso(
                texto[jurisdiccion],
                {"social": N.LRJS_43_4, "contencioso": N.LJCA_128_2, "civil": N.LEC_133_2}[jurisdiccion],
            )
            if jurisdiccion == "contencioso":
                avisos.append(
                    "La LJCA solo dice expresamente que agosto es hábil para los derechos "
                    "fundamentales; también se ha contado como hábil el periodo del 24 de diciembre "
                    "al 6 de enero, que da la fecha más temprana y, por tanto, la prudente."
                )
        else:
            paso("Agosto y los días del 24 de diciembre al 6 de enero son inhábiles", N.LOPJ_183)
    lugares_txt = []
    for lugar in cal.lugares:
        partes = [CCAA[lugar.ccaa]] if lugar.ccaa else []
        if lugar.isla:
            partes.append(f"isla de {lugar.isla}")
        if lugar.municipio:
            partes.append(lugar.municipio)
        if lugar.festivos_locales:
            n = len(lugar.festivos_locales)
            partes.append(f"{n} {'festivo local indicado' if n == 1 else 'festivos locales indicados'}")
        lugares_txt.append(", ".join(partes) or "solo festivos nacionales")
    if len(lugares_txt) > 1:
        paso(
            "Festivos de todos los lugares indicados ("
            + " | ".join(lugares_txt)
            + "): un día inhábil en cualquiera de ellos no cuenta",
            N.L39_30_6,
        )
    else:
        paso(f"Calendario de festivos: {lugares_txt[0]}")
    if not any(lugar.ccaa for lugar in cal.lugares):
        avisos.append("No se ha indicado comunidad autónoma: solo se descuentan los festivos nacionales.")
    for lugar in cal.lugares:
        locales = fiestas_locales(lugar.municipio, inicio.year) if lugar.municipio else None
        fuente = fuente_locales(lugar.ccaa, inicio.year) if lugar.ccaa else None
        if locales and fuente:
            dias = ", ".join(f"{d:%d/%m}" for d in locales)
            paso(f"Fiestas locales de {lugar.municipio} en {inicio.year} ({dias}), según {fuente[0]}")

    # 2) Cómputo.
    inicio_computo = inicio + timedelta(days=1)
    norma_inicio = N.L39_30_3 if jurisdiccion == "administrativo" else N.LEC_133_1
    paso(
        f"El día inicial es el de la notificación o publicación ({inicio:%d/%m/%Y}); "
        f"se empieza a contar el día siguiente, {fecha_larga(inicio_computo)}",
        norma_inicio,
    )
    primer_habil, _ = reglas.siguiente_habil(inicio_computo)
    if unidad == "dias" and primer_habil != inicio_computo:
        paso(f"Ese día es inhábil, así que el primer día que cuenta es el {fecha_larga(primer_habil)}")

    if unidad == "dias":
        d, contados = inicio, 0
        while contados < cantidad:
            d += timedelta(days=1)
            motivo = reglas.inhabil(d)
            if motivo:
                excluidos.append(DiaExcluido(d, motivo))
            else:
                contados += 1
        paso(f"Se cuentan {cantidad} días hábiles, sin sábados, domingos ni festivos", _norma_dias(jurisdiccion))
        if excluidos:
            paso(f"Días que no cuentan: {_resumen_excluidos(excluidos)}", _norma_inhabiles(jurisdiccion))
        paso(f"El día hábil número {cantidad} es el {fecha_larga(d)}")
        vencimiento = d
    else:
        if unidad == "dias_naturales":
            d = inicio + timedelta(days=cantidad)
            paso(
                f"Plazo en días naturales (solo cuando una ley lo dice así): {cantidad} días seguidos, "
                f"incluidos sábados, domingos y festivos, llevan al {fecha_larga(d)}",
                N.L39_30_2,
            )
        else:
            meses = cantidad * (12 if unidad == "anios" else 1)
            base = inicio
            if reglas.judicial and jurisdiccion == "contencioso" and not urgente and inicio.month == 8:
                base = date(inicio.year, 8, 31)
                paso("Notificación en agosto: el plazo no empieza a correr hasta el 1 de septiembre", N.LJCA_128_2)
                avisos.append(
                    "Con notificaciones en agosto hay resoluciones que computan el plazo de "
                    "otra forma; comprueba el criterio de tu tribunal y no apures el último día."
                )
            d = _sumar_meses(base, meses)
            unidad_txt = (
                f"{cantidad} {'año' if cantidad == 1 else 'años'}"
                if unidad == "anios"
                else f"{cantidad} {'mes' if cantidad == 1 else 'meses'}"
            )
            norma_meses = N.L39_30_4 if jurisdiccion == "administrativo" else N.LEC_133_3
            if d.day != base.day:
                paso(
                    f"{unidad_txt} de fecha a fecha: el mes de vencimiento no tiene día {base.day}, "
                    f"así que vence el último día del mes, el {fecha_larga(d)}",
                    norma_meses,
                )
            else:
                paso(
                    f"{unidad_txt} de fecha a fecha: el plazo acaba el mismo día del mes, el {fecha_larga(d)}",
                    norma_meses,
                )
            if jurisdiccion == "contencioso" and not urgente:
                agostos = _agostos_entre(base, d)
                extra = 0
                while agostos > extra:
                    extra = agostos
                    d = _sumar_meses(base, meses + extra)
                    agostos = _agostos_entre(base, d)
                if extra:
                    paso(
                        f"En agosto no corre el plazo: se añade{'n' if extra > 1 else ''} {extra} "
                        f"{'mes' if extra == 1 else 'meses'} y pasa al {fecha_larga(d)}",
                        N.LJCA_128_2,
                    )
            elif reglas.judicial and not urgente and _agostos_entre(base, d):
                avisos.append(
                    "El plazo cruza agosto. Hay tribunales que no computan agosto en los plazos "
                    "procesales por meses; aquí no se descuenta, que es la fecha más temprana."
                )
        nuevo, saltados = reglas.siguiente_habil(d)
        if saltados:
            excluidos += saltados
            norma_fin = {"administrativo": N.L39_30_5}.get(jurisdiccion, N.LEC_133_4)
            paso(
                f"El último día es inhábil ({_resumen_excluidos(saltados)}); se prorroga al siguiente "
                f"hábil, el {fecha_larga(nuevo)}",
                norma_fin,
            )
        vencimiento = nuevo

    # 3) Hasta qué hora se puede presentar.
    presentacion = None
    if jurisdiccion == "administrativo":
        paso("En el registro electrónico se puede presentar hasta las 23:59:59 del último día", N.L39_31_2)
    else:
        siguiente, _ = reglas.siguiente_habil(vencimiento + timedelta(days=1))
        presentacion = datetime.combine(siguiente, time(15, 0))
        norma_gracia = N.LRJS_45_1 if jurisdiccion == "social" else N.LEC_135_5
        paso(
            f"El plazo expira a las 24:00 del {vencimiento:%d/%m/%Y}, pero el escrito puede presentarse "
            f"hasta las 15:00 del día hábil siguiente, el {fecha_larga(siguiente)}",
            norma_gracia,
        )

    for anio in sorted({inicio.year, vencimiento.year}):
        if not cal.locales_conocidos(anio):
            avisos.append(
                f"Faltan los festivos locales de {anio}: si el plazo cruza alguno, vencerá más "
                "tarde de lo calculado aquí. Indica el municipio (capitales de provincia) o los días."
            )
        if not Calendario.es_oficial(anio):
            avisos.append(
                f"El calendario de festivos de {anio} no está verificado con el BOE en esta "
                "versión; se usan los datos de la librería holidays."
            )

    return Resultado(
        inicio=inicio,
        cantidad=cantidad,
        unidad=unidad,
        jurisdiccion=jurisdiccion,
        vencimiento=vencimiento,
        pasos=tuple(pasos),
        excluidos=tuple(excluidos),
        advertencias=tuple(avisos),
        presentacion_hasta=presentacion,
        normas=tuple(normas),
    )


def _agostos_entre(inicio: date, fin: date) -> int:
    """Número de meses de agosto que caen entre el día siguiente a ``inicio`` y ``fin``."""
    return sum(1 for anio in range(inicio.year, fin.year + 1) if inicio < date(anio, 8, 31) and date(anio, 8, 1) <= fin)
