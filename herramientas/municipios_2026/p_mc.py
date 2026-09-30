import json, re
from comun import LOC, MESES, OUT, lineas
from datetime import date
from ine import buscar, buscar_aprox, buscar_prefijo

ls = [l for l in lineas("mur.txt") if l]
i = next(k for k, l in enumerate(ls) if l.upper().startswith("ABANILLA"))
DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
regs, k = [], i
# Filas: [n.º] NOMBRE, día semana, día, mes, día semana, día, mes
while k < len(ls):
    l = ls[k]
    if l.upper() == l and re.search(r"[A-ZÑÁÉÍÓÚÜ]{2}", l) and not re.search(r"\d", l):
        ine = buscar(l, "MC") or buscar_prefijo(l, "MC", "Murcia") or buscar_aprox(l, "MC", "Murcia")
        trozos = ls[k + 1:k + 7]
        if ine and len(trozos) == 6 and trozos[0] in DIAS and trozos[3] in DIAS:
            fs = [date(2026, MESES[trozos[j + 1].lower()], int(trozos[j])).isoformat() for j in (1, 4)]
            regs.append({"nombre": ine["NOMBRE"], "provincia": "Murcia", "ine": ine["codigo"], "dias": fs, "parciales": [], "ccaa": "MC"})
            k += 7
            continue
    k += 1
json.dump(regs, open(OUT / "MC.json", "w", encoding="utf-8"), ensure_ascii=False)
print("MC:", len(regs), [r["nombre"] for r in regs][:50])
print([r for r in regs if r["nombre"] == "Murcia"])
