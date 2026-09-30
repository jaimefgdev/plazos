# Fiestas locales de 2026 de todos los municipios

Lectores que convierten los boletines oficiales en `src/plazos/datos/municipios_2026.json`.
Sirven de guía para repetir el trabajo cada año: cada comunidad publica en un formato distinto.

1. Descarga los boletines de la tabla de fuentes de `ensamblar.py` (y sus correcciones) en
   `boletines/`, y extrae su texto con `python txt.py boletines/archivo.pdf`.
2. Descarga el diccionario de municipios del INE (`diccionarioAA.xlsx`) y conviértelo a `ine.json`.
3. Ejecuta los `p_*.py` de cada comunidad. Burgos publica el anexo como imagen: `ocr_burgos.py`
   lo lee con OCR (`pip install rapidocr_onnxruntime`).
4. `python ensamblar.py` junta todo, asigna el código INE y la isla (Canarias), compara las 50
   capitales con la verificación hecha a mano y escribe el fichero final en `salida/`.

Criterios:

- Solo se incluyen municipios (código INE). Las pedanías, parroquias y entidades locales menores
  con fiestas propias quedan como «parciales» de su municipio, con su ámbito.
- Si el municipio tiene fiestas propias y además algunos núcleos tienen otras, las del municipio
  son sus fiestas y las de los núcleos, parciales. Si solo hay fiestas por núcleos, cuentan como
  fiestas del municipio las comunes a todos.
- Las coincidencias aproximadas con el INE se revisan a mano (`APROX`/`informe`), y las que eran
  pedanías de otro municipio están en `NO_CASAR`.
