# Cambios

## Sin publicar

- Fiestas locales de 2026 de los 8.132 municipios. Se han revisado en los boletines los 742 que
  faltaban: 114 tienen fiestas (relaciones complementarias de Ávila, BOJA n.º 247 de 2025,
  concejos de Navarra con fecha móvil, núcleos de Cataluña…) y 628 no tienen ninguna publicada:
  el boletín dice que no las comunicaron o no figuran en él. Estos últimos llevan `estado`
  (`"no_comunicado"` o `"no_publicado"`) y el cálculo avisa de que no se ha descontado ninguna.
- `Municipio.aviso` cuando la fecha publicada no es inequívoca (Baztan, Labastida, Ciruelos de Cervera).
- Correcciones: Guarromán (BOJA n.º 32 de 2026), Coín (BOJA n.º 247), El Pinar y Píñar, Calonge de
  Segarra, y los núcleos de varios municipios de Cataluña que estaban asignados al municipio anterior.
- La búsqueda por nombre distingue la «ñ» («Píñar» ya no se confunde con El Pinar), y sigue
  encontrando el nombre escrito sin ella.

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
