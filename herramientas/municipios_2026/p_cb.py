import warnings
import pymupdf
from comun import LOC, MESES, guardar, nombre
from datetime import date

warnings.filterwarnings("ignore")
doc = pymupdf.open(LOC / "cant428192.pdf")
regs, raros = [], []
for page in doc:
    for t in page.find_tables().tables:
        for fila in t.extract():
            celdas = [c for c in fila if c is not None]
            if len(celdas) < 4 or celdas[0] in ("", "AYUNTAMIENTO") or "FESTIVIDAD" in celdas:
                continue
            n, _, dias, meses = celdas[0], celdas[1], celdas[2], celdas[3]
            ds, ms = dias.split(), meses.split()
            if len(ds) != len(ms) or not ds:
                raros.append(fila); continue
            try:
                fs = [date(2026, MESES[m.lower()], int(d)).isoformat() for d, m in zip(ds, ms)]
            except (KeyError, ValueError):
                raros.append(fila); continue
            regs.append({"nombre": nombre(n.replace("\n", " ")), "provincia": "Cantabria", "dias": fs})
print("filas raras:", raros[:10])
guardar("CB", regs, "BOC n.º 238, de 11-12-2025 (Resolución de 2-12-2025)")
