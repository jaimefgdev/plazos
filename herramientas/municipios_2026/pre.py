import re
from comun import fechas

def preparar(ls):
    """Une nombres partidos y separa «NOMBRE 12 de septiembre» en dos líneas."""
    ls = [l.strip() for l in ls if l and l.strip()]
    out = []
    i = 0
    while i < len(ls):
        l = ls[i]
        while i + 1 < len(ls) and (
            re.fullmatch(r"\(ANEJO\)", ls[i + 1], re.I)
            or (re.search(r"(\s[-–]|\s[-–]\s\w+|\b(DE|DEL|LA|LAS|LOS|EL|SAN|SANTA|Y))$", l)
                and l.upper() == l and not re.search(r"\d", l)
                and ls[i + 1].upper() == ls[i + 1] and not re.search(r"\d", ls[i + 1]))
        ):
            i += 1
            l = f"{l} {ls[i]}"
        m = re.match(r"^([^\d]{3,}?)\s+(\d{1,2}\s*(?:de\s*)?[A-Za-zñÑ].*)$", l)
        if m and fechas(m.group(2)) and not fechas(m.group(1)) and m.group(1).upper() == m.group(1):
            out += [m.group(1), m.group(2)]
        else:
            out.append(l)
        i += 1
    return out
