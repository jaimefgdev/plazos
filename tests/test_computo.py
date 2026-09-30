from datetime import date, datetime

import pytest

from plazos import Lugar, calcular
from plazos.calendario import Calendario

# --- Administrativo (Ley 39/2015) -------------------------------------------------


def test_diez_dias_habiles_sin_festivos():
    # Notificado el lunes 20-7-2026: 21-24 jul, 27-31 jul, 3 ago.
    r = calcular(date(2026, 7, 20), 10, ccaa="MD")
    assert r.vencimiento == date(2026, 8, 3)
    assert r.presentacion_hasta is None


def test_agosto_es_habil_en_lo_administrativo():
    r = calcular(date(2026, 7, 31), 5, ccaa="MD")
    assert r.vencimiento == date(2026, 8, 7)


def test_festivo_autonomico_solo_en_su_comunidad():
    # 28-7-2026 es festivo en Cantabria (Día de las Instituciones) y no en Madrid.
    assert calcular(date(2026, 7, 27), 1, ccaa="CB").vencimiento == date(2026, 7, 29)
    assert calcular(date(2026, 7, 27), 1, ccaa="MD").vencimiento == date(2026, 7, 28)


def test_festivo_local():
    # San Isidro (15-5-2026, viernes) en Madrid capital.
    r = calcular(date(2026, 5, 14), 1, ccaa="MD", festivos_locales=[date(2026, 5, 15)], municipio="Madrid")
    assert r.vencimiento == date(2026, 5, 18)
    assert any("festivo local en Madrid" in e.motivo for e in r.excluidos)


def test_domicilio_y_sede_distintos_suman_festivos():
    # Art. 30.6: inhábil en cualquiera de los dos lugares cuenta como inhábil.
    r = calcular(date(2026, 3, 18), 1, lugares=[Lugar("MD"), Lugar("VC")])
    assert r.vencimiento == date(2026, 3, 20)  # 19-3 es festivo en la Comunitat Valenciana
    assert any("art. 30.6" in str(p) for p in r.pasos)


def test_mes_fecha_a_fecha():
    assert calcular(date(2026, 3, 10), 1, "meses", ccaa="MD").vencimiento == date(2026, 4, 10)


def test_mes_sin_dia_equivalente_vence_el_ultimo_dia():
    # 31-1 + 1 mes -> 28-2-2026 (sábado) -> se prorroga al lunes 2-3.
    r = calcular(date(2026, 1, 31), 1, "meses", ccaa="MD")
    assert r.vencimiento == date(2026, 3, 2)


def test_ultimo_dia_inhabil_se_prorroga():
    # Un mes desde el 12-9-2026 acaba el 12-10 (Fiesta Nacional) -> 13-10.
    assert calcular(date(2026, 9, 12), 1, "meses").vencimiento == date(2026, 10, 13)


def test_anio():
    assert calcular(date(2026, 6, 15), 1, "anios").vencimiento == date(2027, 6, 15)


def test_dias_naturales():
    # 15 días naturales desde el 1-4-2026 -> 16-4 (jueves, hábil).
    assert calcular(date(2026, 4, 1), 15, "dias_naturales").vencimiento == date(2026, 4, 16)
    # 10 naturales desde el 23-3 -> 2-4, Jueves Santo en Madrid -> 3-4 Viernes Santo -> 6-4.
    assert calcular(date(2026, 3, 23), 10, "dias_naturales", ccaa="MD").vencimiento == date(2026, 4, 6)


# --- Civil (LEC) -------------------------------------------------------------------


def test_agosto_inhabil_en_civil():
    r = calcular(date(2026, 7, 20), 20, "dias", "civil", ccaa="MD")
    # 21-31 jul son 9 hábiles; agosto no cuenta; 1-15 sep son los 11 restantes.
    assert r.vencimiento == date(2026, 9, 15)
    assert r.presentacion_hasta == datetime(2026, 9, 16, 15, 0)


def test_navidad_inhabil_en_civil():
    r = calcular(date(2026, 12, 18), 5, "dias", "civil", ccaa="MD")
    # 21, 22, 23 dic; 7, 8 ene.
    assert r.vencimiento == date(2027, 1, 8)


def test_urgente_civil_cuenta_agosto():
    r = calcular(date(2026, 7, 30), 3, "dias", "civil", ccaa="MD", urgente=True)
    assert r.vencimiento == date(2026, 8, 4)


def test_gracia_hasta_las_15_salta_agosto():
    r = calcular(date(2026, 7, 29), 2, "dias", "civil", ccaa="MD")
    assert r.vencimiento == date(2026, 7, 31)
    assert r.presentacion_hasta == datetime(2026, 9, 1, 15, 0)


def test_meses_procesales_que_cruzan_agosto_avisan():
    r = calcular(date(2026, 7, 10), 1, "meses", "civil")
    assert r.vencimiento == date(2026, 9, 1)  # 10-8 es inhábil en civil
    assert any("agosto" in a for a in r.advertencias)


# --- Contencioso (LJCA) --------------------------------------------------------------


def test_recurso_contencioso_dos_meses_descuenta_agosto():
    r = calcular(date(2026, 7, 20), 2, "meses", "contencioso", ccaa="MD")
    assert r.vencimiento == date(2026, 10, 20)


def test_recurso_contencioso_sin_agosto():
    r = calcular(date(2026, 2, 16), 2, "meses", "contencioso", ccaa="MD")
    assert r.vencimiento == date(2026, 4, 16)


def test_recurso_contencioso_notificado_en_agosto():
    r = calcular(date(2026, 8, 10), 2, "meses", "contencioso", ccaa="MD")
    # Desde el 1-9: 31-10 (sábado) -> 2-11 (festivo en Madrid) -> 3-11.
    assert r.vencimiento == date(2026, 11, 3)
    assert any("agosto" in a for a in r.advertencias)


def test_derechos_fundamentales_agosto_habil():
    r = calcular(date(2026, 7, 29), 10, "dias", "contencioso", ccaa="MD", urgente=True)
    assert r.vencimiento == date(2026, 8, 12)


# --- Social (LRJS) -----------------------------------------------------------------


def test_social_navidad_y_gracia():
    r = calcular(date(2026, 12, 18), 5, "dias", "social", ccaa="CT")
    assert r.vencimiento == date(2027, 1, 8)
    assert r.presentacion_hasta == datetime(2027, 1, 11, 15, 0)
    assert any("LRJS, art. 45.1" in str(p) for p in r.pasos)


def test_social_modalidad_urgente():
    r = calcular(date(2026, 12, 18), 5, "dias", "social", ccaa="CT", urgente=True)
    # 21, 22, 23, 24 dic; 25 y 26 no (26 es sábado); 28 dic.
    assert r.vencimiento == date(2026, 12, 28)


# --- Calendario y validación -------------------------------------------------------


def test_calendario_2026_viene_del_boe():
    assert Calendario.es_oficial(2026)
    cal = Calendario([Lugar("NC")])
    assert cal.festivo(date(2026, 12, 3)) is None  # no está en el anexo del BOE para 2026
    assert "festivo nacional" in cal.festivo(date(2026, 10, 12))


def test_islas_canarias():
    r = calcular(date(2026, 9, 7), 1, ccaa="CN", isla="Gran Canaria")
    assert r.vencimiento == date(2026, 9, 9)
    assert calcular(date(2026, 9, 7), 1, ccaa="CN", isla="Tenerife").vencimiento == date(2026, 9, 8)


def test_aviso_sin_calendario_oficial():
    r = calcular(date(2027, 3, 1), 5, ccaa="MD")
    assert any("no está verificado" in a for a in r.advertencias)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(cantidad=0),
        dict(cantidad=-3),
        dict(unidad="semanas"),
        dict(jurisdiccion="penal"),
        dict(ccaa="XX"),
        dict(unidad="dias_naturales", jurisdiccion="civil"),
        dict(urgente=True),
        dict(isla="Tenerife", ccaa="MD"),
    ],
)
def test_errores(kwargs):
    base = dict(inicio=date(2026, 3, 2), cantidad=5)
    with pytest.raises(ValueError):
        calcular(**{**base, **kwargs})


def test_explicacion_cita_normas():
    r = calcular(date(2026, 7, 20), 20, "dias", "civil", ccaa="MD")
    texto = r.explicar()
    assert "LOPJ, art. 183" in texto and "LEC, art. 135.5" in texto
    assert all(n.url.startswith("https://www.boe.es/") for n in r.normas)


# --- Fiestas locales de las capitales ------------------------------------------------


def test_capital_rellena_comunidad_y_fiestas():
    r = calcular(date(2026, 5, 14), 3, municipio="madrid")
    assert r.vencimiento == date(2026, 5, 20)  # 15-5 San Isidro
    assert any("BOCM" in str(p) for p in r.pasos)
    assert not any("Faltan los festivos locales" in a for a in r.advertencias)


def test_alias_y_tildes():
    assert calcular(date(2026, 6, 10), 1, municipio="JAEN").vencimiento == date(2026, 6, 12)
    assert calcular(date(2026, 1, 19), 1, municipio="Donostia").vencimiento == date(2026, 1, 21)


def test_bilbao_usa_la_modificacion():
    # BOB n.º 148 de 2025: el festivo pasa del 21 al 28 de agosto.
    assert calcular(date(2026, 8, 20), 1, municipio="Bilbao").vencimiento == date(2026, 8, 21)
    assert calcular(date(2026, 8, 27), 1, municipio="Bilbao").vencimiento == date(2026, 8, 31)


def test_canarias_isla_automatica():
    # Gran Canaria: 8-9 (Virgen del Pino) es insular; Tenerife no.
    assert calcular(date(2026, 9, 7), 1, municipio="Las Palmas").vencimiento == date(2026, 9, 9)
    assert calcular(date(2026, 9, 7), 1, municipio="Santa Cruz de Tenerife").vencimiento == date(2026, 9, 8)


def test_pamplona_3_de_diciembre():
    assert calcular(date(2026, 12, 2), 1, municipio="Pamplona").vencimiento == date(2026, 12, 4)


def test_capital_en_otra_comunidad_es_error():
    with pytest.raises(ValueError):
        calcular(date(2026, 3, 2), 1, ccaa="CT", municipio="Sevilla")


def test_cincuenta_capitales():
    from plazos.datos import locales_2026 as L

    assert len(L.CAPITALES) == 50
    for nombre, ccaa, _, dias in L.CAPITALES.values():
        assert ccaa in L.FUENTES, nombre
        assert len(dias) == 2 and all(date(2026, m, d) for m, d in dias)


def test_municipio_desconocido_avisa():
    r = calcular(date(2026, 3, 2), 1, ccaa="MD", municipio="La Hiruela")  # no comunicó sus fiestas
    assert any("Faltan los festivos locales" in a for a in r.advertencias)


def test_nombres_en_espanol_aunque_el_sistema_este_en_ingles(monkeypatch):
    from plazos import calendario

    monkeypatch.setenv("LANG", "en_US.UTF-8")
    calendario._nombres.cache_clear()
    try:
        assert "(Año Nuevo)" in Calendario([Lugar("MD")]).festivo(date(2027, 1, 1))
    finally:
        calendario._nombres.cache_clear()


# --- Todos los municipios -------------------------------------------------------------


def test_cobertura_municipios():
    from plazos import municipios

    todos = municipios.todos(2026)
    assert len(todos) >= 7300
    assert {m.ccaa for m in todos} == set(__import__("plazos").CCAA)


def test_capitales_coinciden_con_la_verificacion_manual():
    from plazos import municipios
    from plazos.datos import locales_2026 as L

    for nombre, ccaa, _, dias in L.CAPITALES.values():
        m = municipios.buscar(nombre, ccaa=ccaa)
        assert m is not None, nombre
        assert m.dias == tuple(date(2026, mes, dia) for mes, dia in dias), nombre


def test_municipio_pequeno():
    # Begíjar (Jaén): 24 de julio y 25 de septiembre (BOJA n.º 197).
    r = calcular(date(2026, 7, 23), 1, municipio="Begíjar")
    assert r.vencimiento == date(2026, 7, 27)
    assert any("BOJA" in str(p) for p in r.pasos)


def test_codigo_ine():
    assert calcular(date(2026, 5, 14), 1, municipio="28079").vencimiento == date(2026, 5, 18)


def test_ceuta_y_melilla():
    assert calcular(date(2026, 3, 19), 1, municipio="Ceuta").vencimiento == date(2026, 3, 23)
    assert calcular(date(2026, 9, 16), 1, municipio="Melilla").vencimiento == date(2026, 9, 18)


def test_isla_desde_el_municipio():
    # Arucas está en Gran Canaria: el 8 de septiembre (Virgen del Pino) es festivo insular.
    assert calcular(date(2026, 9, 7), 1, municipio="Arucas").vencimiento == date(2026, 9, 9)


def test_fiesta_de_una_pedania_avisa():
    r = calcular(date(2026, 4, 24), 3, municipio="Lleida")
    assert r.vencimiento == date(2026, 4, 29)  # el 27-4 solo es fiesta en Raimat
    assert any("Raimat" in a for a in r.advertencias)


def test_nombre_repetido_pide_provincia():
    from plazos import municipios

    repetidos = {}
    for m in municipios.todos(2026):
        repetidos.setdefault(m.nombre, []).append(m)
    nombre, lista = next((n, v) for n, v in repetidos.items() if len({m.provincia for m in v}) > 1)
    with pytest.raises(ValueError, match="provincia"):
        municipios.buscar(nombre)
    assert municipios.buscar(nombre, provincia=lista[0].provincia).ine == lista[0].ine


# --- Plazos por horas (Ley 39/2015, art. 30.1) ------------------------------------------


def test_horas_saltan_dias_inhabiles():
    # Viernes 9-10-2026 a las 10:00 + 24 h: 14 h el viernes; sábado, domingo y 12-10 no cuentan.
    r = calcular(date(2026, 10, 9), 24, "horas", hora="10:00", ccaa="MD")
    assert r.vencimiento == date(2026, 10, 13)
    assert r.presentacion_hasta == datetime(2026, 10, 13, 10, 0)


def test_horas_hasta_medianoche():
    r = calcular(date(2026, 10, 5), 24, "horas", hora="00:00")
    assert r.vencimiento == date(2026, 10, 5)
    assert "a las 24:00" in r.explicar()


def test_horas_notificacion_en_dia_inhabil():
    # Sábado a las 18:00, 2 h: empieza a contar el lunes a las 00:00.
    assert calcular(date(2026, 10, 3), 2, "horas", hora="18:00").presentacion_hasta == datetime(2026, 10, 5, 2, 0)


@pytest.mark.parametrize(
    "kwargs", [dict(cantidad=25, hora="10:00"), dict(cantidad=5), dict(cantidad=5, hora="10:00", jurisdiccion="civil")]
)
def test_horas_errores(kwargs):
    with pytest.raises(ValueError):
        calcular(**{"inicio": date(2026, 3, 2), "unidad": "horas", **kwargs})


# --- Pago de deudas tributarias (LGT, art. 62) -----------------------------------------


def test_pago_voluntario_primera_quincena():
    from plazos import plazo_pago

    assert plazo_pago(date(2026, 9, 10)).vencimiento == date(2026, 10, 20)


def test_pago_voluntario_segunda_quincena_y_fin_de_semana():
    from plazos import plazo_pago

    # 16-7 -> día 5 del segundo mes siguiente: 5-9-2026 es sábado -> lunes 7-9.
    r = plazo_pago(date(2026, 7, 16))
    assert r.vencimiento == date(2026, 9, 7)
    assert any("LGT, art. 7.2" in str(p) for p in r.pasos)


def test_pago_apremio_con_festivos():
    from plazos import plazo_pago

    # 30-11 -> 5-12 (sábado), 6 (domingo), 7 (festivo en Madrid), 8 (nacional) -> 9-12.
    assert plazo_pago(date(2026, 11, 30), "apremio", municipio="Madrid").vencimiento == date(2026, 12, 9)
    assert plazo_pago(date(2026, 3, 3), "apremio").vencimiento == date(2026, 3, 20)


def test_pago_periodo_desconocido():
    from plazos import plazo_pago

    with pytest.raises(ValueError):
        plazo_pago(date(2026, 3, 3), "otro")
