import json, warnings
import pymupdf
from rapidocr_onnxruntime import RapidOCR
from comun import LOC, OUT

warnings.filterwarnings("ignore")
ocr = RapidOCR()
import sys
ENTRADA, SALIDA = (sys.argv[1], sys.argv[2]) if len(sys.argv) > 2 else ("cyl_burgos.pdf", "burgos_ocr.json")
doc = pymupdf.open(LOC / ENTRADA)
filas = []
for np_, page in enumerate(doc):
    if len(page.get_text()) > 1500 and ENTRADA == "cyl_burgos.pdf" and np_ not in range(4, 16):
        continue
    if page.get_images():
        png = OUT / f"{ENTRADA}_{np_}.png"
        page.get_pixmap(dpi=200).save(png)
        res, _ = ocr(str(png))
        for caja, texto, conf in res or []:
            x = min(p[0] for p in caja); y = min(p[1] for p in caja)
            filas.append((np_, y, x, texto, conf))
json.dump(filas, open(OUT / SALIDA, "w", encoding="utf-8"), ensure_ascii=False)
print(len(filas)); print(filas[:12])
