import json, re
from comun import LOC, OUT, fechas
from ine import buscar, buscar_aprox, buscar_prefijo


def leer(f):
    t = (LOC / f).read_text(encoding="utf-8")
    # Las entradas empiezan por «— Nombre:»; pueden ocupar dos líneas.
    t = re.sub(r"\n(?!—)", " ", t)
    out = {}
    for m in re.finditer(r"—\s*([^:]+?):\s*([^—]*)", t):
        out[m.group(1).strip()] = m.group(2)
    return out


base, mod = leer("mad.txt"), leer("madmod.txt")
print("modificados:", {k: (fechas(base.get(k, "")), fechas(v)) for k, v in mod.items()})
base.update(mod)
regs, sin, nc = [], [], []
for n, resto in base.items():
    if "no comunicado" in resto.lower():
        nc.append(n); continue
    ine = buscar(n, "MD") or buscar_prefijo(n, "MD", "Madrid") or buscar_aprox(n, "MD", "Madrid")
    if not ine:
        sin.append(n); continue
    regs.append({"nombre": ine["NOMBRE"], "provincia": "Madrid", "ine": ine["codigo"], "dias": fechas(resto), "parciales": [], "ccaa": "MD"})
for r in regs:  # «15 de mayo y 10 de agosto (Valdeolmos) y 24 de agosto (Alalpardo)»
    if r["nombre"] == "Valdeolmos-Alalpardo":
        r["dias"] = ["2026-05-15"]
        r["parciales"] = [{"fecha": "2026-08-10", "ambito": "Valdeolmos"}, {"fecha": "2026-08-24", "ambito": "Alalpardo"}]
json.dump(regs, open(OUT / "MD.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"MD: {len(regs)} | no comunicado: {nc} | sin INE: {sin} | sin días: {[r['nombre'] for r in regs if not r['dias']]} | >2: {[(r['nombre'], r['dias']) for r in regs if len(r['dias']) > 2]}")
print([r for r in regs if r["nombre"] == "Madrid"])
