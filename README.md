# plazos

[![CI](https://github.com/jaimefgdev/plazos/actions/workflows/ci.yml/badge.svg)](https://github.com/jaimefgdev/plazos/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/plazos)](https://pypi.org/project/plazos/)
[![Python](https://img.shields.io/pypi/pyversions/plazos)](https://pypi.org/project/plazos/)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-blue)](LICENSE)

Cálculo de **plazos administrativos y judiciales españoles** que no se limita a darte una fecha:
explica cada paso y cita el artículo que lo justifica, con enlace al texto consolidado del BOE.

**Pruébalo sin instalar nada:** [jaimefgdev.com/plazos](https://jaimefgdev.com/plazos/)

```python
>>> from datetime import date
>>> from plazos import calcular
>>> r = calcular(date(2026, 7, 20), 20, "dias", "civil", municipio="Madrid")
>>> r.vencimiento
datetime.date(2026, 9, 15)
>>> print(r.explicar())
Vence el martes, 15 de septiembre de 2026.
Último momento para presentar: miércoles, 16 de septiembre de 2026 a las 15:00.

1. Plazo procesal del orden civil (LEC); los días inhábiles judiciales los fija la LOPJ (LOPJ, art. 182)
2. Agosto y los días del 24 de diciembre al 6 de enero son inhábiles (LOPJ, art. 183)
3. Calendario de festivos: Comunidad de Madrid, Madrid
4. Fiestas locales de Madrid en 2026 (15/05, 09/11), según BOCM n.º 296, de 12-12-2025 (...)
5. El día inicial es el de la notificación o publicación (20/07/2026); se empieza a contar el día siguiente, martes, 21 de julio de 2026 (LEC, art. 133.1)
6. Se cuentan 20 días hábiles, sin sábados, domingos ni festivos (LEC, art. 133.2)
7. Días que no cuentan: 16 días de fin de semana; 21 días (03/08 a 31/08): agosto, inhábil en los juzgados (LEC, art. 130.2)
8. El día hábil número 20 es el martes, 15 de septiembre de 2026
9. El plazo expira a las 24:00 del 15/09/2026, pero el escrito puede presentarse hasta las 15:00 del día hábil siguiente, el miércoles, 16 de septiembre de 2026 (LEC, art. 135.5)
```

## Qué cubre

| Tipo | Reglas aplicadas |
|---|---|
| **Administrativo** | Ley 39/2015, art. 30: días hábiles sin sábados, domingos ni festivos; días naturales cuando una ley lo dice; meses y años de fecha a fecha (último día del mes si no hay equivalente); prórroga si el último día es inhábil; festivos del domicilio **y** de la sede del órgano (art. 30.6); registro electrónico hasta las 23:59:59 (art. 31.2). |
| **Civil** | LEC arts. 130, 133 y 135.5 y LOPJ arts. 182–185: agosto y del 24 de diciembre al 6 de enero inhábiles; actuaciones urgentes; presentación hasta las 15:00 del día hábil siguiente. |
| **Contencioso** | LJCA art. 128.2: en agosto no corre ningún plazo (también los de meses, como los dos meses del art. 46.1), salvo derechos fundamentales. |
| **Por horas** | Ley 39/2015, art. 30.1: solo cuentan las horas de días hábiles, de hora en hora y de minuto en minuto desde la notificación, y como mucho 24 (si no, el plazo va en días). |
| **Pago a Hacienda** | LGT, art. 62: deuda liquidada notificada del 1 al 15, hasta el día 20 del mes siguiente; del 16 al final, hasta el día 5 del segundo mes siguiente (o del 20 del mismo mes y el 5 del siguiente tras la providencia de apremio), pasando al siguiente día hábil si hace falta. |
| **Social** | LRJS arts. 43.4 y 45.1: modalidades urgentes (despido, vacaciones, conflictos colectivos…) en las que agosto y Navidad son hábiles; presentación hasta las 15:00 del día siguiente. |

**Calendarios incluidos**

- **Festivos nacionales y autonómicos de 2026** tomados del anexo de la
  [Resolución BOE-A-2025-23702](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-23702), incluidos los insulares de Canarias. Para otros años se usa la librería [holidays](https://pypi.org/project/holidays/) y el resultado lo advierte.
- **Fiestas locales de 2026 de 7.390 municipios** (el 91 % de los 8.132 de España), sacadas de los
  boletines oficiales de las 17 comunidades, de las 9 provincias de Castilla y León y de Ceuta y
  Melilla, con sus correcciones y resoluciones complementarias (por ejemplo, Bilbao pasó del 21 al
  28 de agosto). Los que faltan son ayuntamientos que no comunicaron sus fiestas a tiempo. La fuente
  sale en la explicación.
- **Fiestas de pedanías, parroquias y entidades locales menores**: si en parte del municipio hay
  otra fiesta local (Raimat en Lleida, las parroquias de Llanes…), el resultado lo avisa si cae
  dentro del plazo.
- En Canarias, el municipio decide también la fiesta insular (Arucas → Gran Canaria).
- Para un municipio sin datos puedes pasar sus fiestas locales con `festivos_locales=[...]`.

| | Municipios con datos | | Municipios con datos |
|---|---|---|---|
| Andalucía | 756 de 785 | Comunitat Valenciana | 539 de 542 |
| Aragón | 581 de 731 | Extremadura | 388 de 388 |
| Asturias | 78 de 78 | Galicia | 313 de 313 |
| Canarias | 88 de 88 | Illes Balears | 67 de 67 |
| Cantabria | 102 de 102 | La Rioja | 163 de 174 |
| Castilla y León | 1.832 de 2.248 | Madrid | 171 de 179 |
| Castilla-La Mancha | 905 de 919 | Murcia | 45 de 45 |
| Cataluña | 886 de 947 | Navarra | 229 de 272 |
| Ceuta y Melilla | 2 de 2 | País Vasco | 245 de 252 |

## Instalación

```bash
pip install plazos
```

Requiere Python 3.10 o superior.

## Uso

```python
from datetime import date
from plazos import Lugar, calcular

# Recurso contencioso: dos meses, agosto no cuenta.
calcular(date(2026, 7, 20), 2, "meses", "contencioso", municipio="Sevilla").vencimiento
# -> 2026-10-20

# Cualquier municipio, por nombre o por código INE; si el nombre se repite, con la provincia.
calcular(date(2026, 7, 23), 5, municipio="Begíjar")
calcular(date(2026, 7, 23), 5, municipio="Villanueva de la Sierra", provincia="Cáceres")

# Municipio sin datos: comunidad y fiestas locales a mano (fechas de ejemplo).
calcular(date(2026, 5, 14), 10, ccaa="MD", festivos_locales=[date(2026, 5, 20), date(2026, 9, 8)])

# Interesado en Valencia y órgano en Madrid: cuenta como inhábil lo que lo sea en cualquiera.
calcular(date(2026, 3, 18), 5, lugares=[Lugar(municipio="València"), Lugar("MD")])

# Plazo por horas: notificado el viernes 9-10-2026 a las 10:00, 24 horas.
calcular(date(2026, 10, 9), 24, "horas", hora="10:00", municipio="Madrid").presentacion_hasta
# -> 2026-10-13 10:00 (no cuentan el fin de semana ni el 12 de octubre)

# Último día para pagar una liquidación de Hacienda (o "apremio").
from plazos import plazo_pago

plazo_pago(date(2026, 7, 16), "voluntario", municipio="Madrid").vencimiento  # -> 2026-09-07

# Despido (modalidad urgente de la LRJS): agosto y Navidad cuentan.
calcular(date(2026, 12, 18), 20, "dias", "social", ccaa="CT", urgente=True)
```

`Resultado` incluye `vencimiento`, `presentacion_hasta` (en los judiciales), `pasos` (texto y norma de
cada uno), `excluidos` (cada día que no cuenta y por qué), `advertencias` y `normas` con sus enlaces.

### Línea de órdenes

```bash
plazos 2026-07-20 20 dias -j civil --municipio Madrid
plazos 2026-07-20 2 meses -j contencioso --ccaa AN --local 2026-06-04 --json
plazos 2026-10-09 24 horas --hora 10:00 --municipio Madrid
plazos 2026-07-16 --pago voluntario --municipio Madrid
```

Comunidades con código ISO 3166-2: `AN AR AS IB CN CB CL CM CT EX GA MD MC NC PV RI VC CE ML`.

## Criterios cuando la norma no es clara

Si hay más de una lectura razonable, `plazos` elige **la que da la fecha más temprana** y lo dice en
las advertencias:

- Plazos procesales por meses que cruzan agosto en civil y social: no se descuenta agosto.
- Derechos fundamentales en el contencioso: además de agosto, se cuenta como hábil el periodo del 24 de diciembre al 6 de enero.
- Notificaciones en agosto de plazos contenciosos por meses: se cuenta desde el 1 de septiembre y se avisa de que hay criterios distintos.

## Qué no hace

- No cubre los plazos penales: la LECrim (art. 201) y la LOPJ (art. 184) declaran hábiles todos los
  días y horas para la instrucción, pero si eso alcanza a los plazos de recurso de las partes depende
  de la jurisprudencia, así que no hay una regla que se pueda aplicar con total seguridad.
- En lo tributario solo calcula el plazo de pago de las deudas liquidadas por la Administración; los
  plazos de cada autoliquidación (modelos 303, 130…) dependen de la normativa de cada impuesto.
- Tampoco cubre prescripción o caducidad civil con reglas propias.
- No calcula cuándo se entiende hecha una notificación (por ejemplo, los tres días de LexNET o los diez de la sede electrónica): parte del día que le digas.

## Herramienta web

La carpeta [`web/`](web/) contiene la calculadora publicada en jaimefgdev.com/plazos: HTML, CSS y
JavaScript sin dependencias. Todo el cálculo se hace en el navegador. `web/plazos.js` traduce el motor
de Python y `web/datos.js` se genera con `python scripts/exportar_web.py`. Un test lanza 600 casos
aleatorios en los dos y exige que den exactamente el mismo resultado, textos incluidos.

## Desarrollo

```bash
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check . && mypy
```

Cada año hay que añadir el calendario nuevo en `src/plazos/datos/`: el anexo de la resolución del BOE
y las fiestas locales de los municipios (los lectores de boletines están en
[`herramientas/municipios_2026/`](herramientas/municipios_2026/LEEME.md)), y volver a generar
`web/datos.js` y `web/municipios.json`.

## Aviso

Herramienta orientativa, no asesoramiento jurídico. Comprueba siempre el calendario oficial y la norma
aplicable a tu caso. Se distribuye sin garantía de ningún tipo (ver [LICENSE](LICENSE)).

## Licencia

MIT © Jaime Fernández González
