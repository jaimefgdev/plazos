"""Listas «Nombre» + línea de fechas, sin entidades: lo que no casa con el INE se ignora."""
import re
from comun import fechas
from generico import es_fecha
from ine import buscar, buscar_aprox, buscar_prefijo
from pre import preparar

# Pedanías que el casado aproximado confundía con otro municipio (revisadas a mano).
NO_CASAR = {"Carrascosa del Campo", "Fuentes claras Chillaron", "SANTA MARÍA"}


def parse(ls, ccaa, provincia_de, ruido=None, casar=None, informe=None):
    """provincia_de(línea) devuelve la provincia si la línea es una cabecera de provincia."""
    ls = preparar(ls)
    regs, actual, prov, sin = {}, None, None, []
    for k, l in enumerate(ls):
        p = provincia_de(l)
        if p:
            prov, actual = p, None
            continue
        if ruido and ruido(l):
            continue
        if es_fecha(l) or (actual is not None and fechas(l) and not re.search(r"[A-Za-z]{4,}\s*$", l.split()[-1] if l.split() else "")):
            if actual is not None:
                actual["dias"] += [f for f in fechas(l) if f not in actual["dias"]]
            continue
        sig = ls[k + 1] if k + 1 < len(ls) else ""
        if not fechas(sig):
            continue
        n = l.strip(" .:")
        if casar:
            ine = casar(n, prov)
        else:
            ine = buscar(n, ccaa, prov)
            if not ine and n not in NO_CASAR:
                ine = buscar_prefijo(n, ccaa, prov) or buscar_aprox(n, ccaa, prov)
                if ine and informe is not None:
                    informe.append((n, ine["NOMBRE"]))
        if not ine:
            sin.append(n); actual = None; continue
        actual = regs.setdefault(ine["codigo"], {"nombre": ine["NOMBRE"], "provincia": prov, "ine": ine["codigo"], "dias": [], "parciales": []})
        actual["dias"] = []
    return list(regs.values()), sin
