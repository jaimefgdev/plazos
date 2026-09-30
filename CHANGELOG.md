# Cambios

## 0.3.0 — 2026-09-30

- Plazos administrativos por horas (Ley 39/2015, art. 30.1): solo cuentan las horas de los días
  hábiles, de hora en hora desde la notificación, hasta 24 horas.
- Último día para pagar a Hacienda una deuda liquidada, en periodo voluntario (LGT, art. 62.2) o
  tras la providencia de apremio (art. 62.5): `plazo_pago()` y `plazos FECHA --pago voluntario`.
- La calculadora web incluye los dos.

## 0.2.0 — 2026-09-30

- Fiestas locales de 2026 de 7.390 municipios de toda España (antes, solo las 50 capitales), con
  sus correcciones y resoluciones complementarias, incluidas Ceuta y Melilla.
- Fiestas de pedanías y entidades locales menores: aviso si caen dentro del plazo.
- Búsqueda del municipio por nombre (con o sin tildes y artículo) o por código INE, y `provincia`
  para distinguir nombres repetidos.
- En Canarias, la isla se deduce del municipio.
- La calculadora web busca entre todos los municipios.

## 0.1.0 — 2026-09-30

Primera versión.

- Plazos administrativos (Ley 39/2015) y judiciales de los órdenes civil, contencioso y social.
- Explicación paso a paso con la norma de cada paso y enlace al BOE.
- Festivos nacionales y autonómicos de 2026 según BOE-A-2025-23702, con los insulares de Canarias.
- Fiestas locales de 2026 de las 50 capitales de provincia, sacadas de sus boletines oficiales.
- Línea de órdenes con salida en texto o JSON.
- Calculadora web en `web/`, con el mismo resultado que la librería comprobado por tests.
