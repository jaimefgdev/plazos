"""Junta las salidas de cada comunidad en un único fichero con código INE y fuente.

    python ensamblar.py   (antes: ejecutar todos los p_*.py)
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from comun import OUT
from ine import REG, buscar, buscar_aprox, buscar_prefijo

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from plazos.datos import locales_2026 as CAP  # noqa: E402

FUENTES = {
    "AN": ("BOJA n.º 197, de 14-10-2025; modificaciones en BOJA n.º 33 y 79 de 2026",
           "https://www.juntadeandalucia.es/boja/2025/197/28"),
    "AR": ("BOA n.º 225, de 20-11-2025, y Resolución complementaria de 10-3-2026 (BOA n.º 56)",
           "https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VEROBJ&MLKOB=1421874360606"),
    "AS": ("BOPA n.º 114, de 16-6-2025", "https://miprincipado.asturias.es/documents/d/guest/2025-04744"),
    "IB": ("BOIB n.º 129, de 27-9-2025; correcciones en BOIB n.º 139 y 150",
           "https://www.caib.es/sites/calendarilaboral/f/529360"),
    "CN": ("BOC n.º 165, de 21-8-2025", "https://www.gobiernodecanarias.org/boc/2025/165/3029.html"),
    "CB": ("BOC n.º 238, de 11-12-2025", "https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=428192"),
    "CM": ("DOCM n.º 240, de 12-12-2025; modificación en DOCM n.º 51 de 2026",
           "https://docm.jccm.es/docm/descargarArchivo.do?ruta=2025/12/12/pdf/2025_9468.pdf&tipo=rutaDocm"),
    "CT": ("DOGC n.º 9565, de 17-12-2025 (Orden EMT/208/2025); modificación por Orden EMT/3/2026",
           "https://dogc.gencat.cat/ca/document-del-dogc/?documentId=1032232"),
    "EX": ("DOE n.º 204, de 23-10-2025", "https://doe.juntaex.es/pdfs/doe/2025/2040o/25063799.pdf"),
    "GA": ("DOG n.º 210, de 30-10-2025",
           "https://www.xunta.gal/dog/Publicados/2025/20251030/AnuncioG0767-221025-0001_es.html"),
    "MD": ("BOCM n.º 296, de 12-12-2025; modificación en BOCM n.º 309",
           "https://www.bocm.es/boletin/CM_Orden_BOCM/2025/12/12/BOCM-20251212-34.PDF"),
    "MC": ("BORM n.º 163, de 17-7-2025", "https://www.borm.es/services/anuncio/ano/2025/numero/3546/pdf?id=837607"),
    "NC": ("BON n.º 241, de 2-12-2025 (Resolución 682/2025), modificada por la Resolución 765/2025; "
           "3 de diciembre común a Navarra (Resolución 390/2025)", "https://bon.navarra.es/es/anuncio/-/texto/2025/241/12"),
    "PV": ("BOTHA n.º 82 (Álava), BOB n.º 138 y 148 (Bizkaia) y BOG n.º 168 (Gipuzkoa), de 2025",
           "https://egoitza.gipuzkoa.eus/gao-bog/castell/bog/2025/09/04/c2506163.pdf"),
    "RI": ("BOR n.º 159, de 19-8-2025", "https://web.larioja.org/bor-portada/"),
    "CE": ("BOCCE de 19-9-2025 (Resolución de 15-9-2025 de la Delegación del Gobierno en Ceuta)",
           "https://www.iberley.es/legislacion/calendario-fiestas-locales-ciudad-autonoma-ceuta-ano-2026-27284564"),
    "ML": ("BOME n.º 6315, de 3-10-2025 (Acuerdo del Consejo de Gobierno)",
           "https://www.melilla.es/melillaportal/contenedor.jsp?seccion=s_fact_d4_v1.jsp&contenido=41767&nivel=1400&tipo=2"),
    "VC": ("DOGV n.º 10238, de 14-11-2025; modificación en DOGV n.º 10281",
           "https://dogv.gva.es/datos/2025/11/14/pdf/2025_46326_es.pdf"),
}
FUENTES_CL = {
    "Ávila": "BOP de Ávila n.º 186, de 26-9-2025",
    "Burgos": "BOP de Burgos n.º 165, de 3-9-2025, y resolución complementaria en el n.º 1, de 2-1-2026",
    "León": "BOP de León n.º 177, de 17-9-2025, y resolución complementaria en el n.º 8, de 14-1-2026",
    "Palencia": "BOP de Palencia n.º 112, de 17-9-2025",
    "Salamanca": "BOP de Salamanca n.º 181, de 19-9-2025, y relación complementaria en el n.º 234, de 4-12-2025",
    "Segovia": "BOP de Segovia n.º 113, de 19-9-2025",
    "Soria": "BOP de Soria n.º 108, de 22-9-2025",
    "Valladolid": "BOP de Valladolid n.º 179, de 19-9-2025",
    "Zamora": "BOP de Zamora n.º 106, de 19-9-2025, y calendario complementario en el n.º 142, de 15-12-2025",
}
URL_CL = "https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html"


def cargar(nombre):
    return json.load(open(OUT / nombre, encoding="utf-8"))


def limpiar_ambito(a):
    if a.replace(" ", "").isupper() and " " not in a and len(a) > 12:
        a = a.title()  # nombres del OCR de Burgos sin espacios
    a = re.sub(r"^Eatim de\s+", "", a, flags=re.I)
    a = re.split(r",?\s*(?:Eatim|entidad local menor|dependiente de)", a, flags=re.I)[0]
    return a.strip(" ,") or a


todos = {}
problemas = []


def meter(r, ccaa, fuente):
    ine = None
    if r.get("ine"):
        ine = next(x for x in REG if x["codigo"] == r["ine"])
    else:
        ine = (buscar(r["nombre"], ccaa, r.get("provincia")) or buscar_prefijo(r["nombre"], ccaa, r.get("provincia") or "")
               or buscar_aprox(r["nombre"], ccaa, r.get("provincia")))
    if not ine:
        problemas.append((ccaa, r["nombre"], "sin código INE"))
        return
    dias = sorted(set(r["dias"]))
    parciales = []
    for p in r.get("parciales", []):
        if p["fecha"] not in dias:
            parciales.append({"fecha": p["fecha"], "ambito": limpiar_ambito(p["ambito"])})
    if not dias and not parciales:
        return
    todos[ine["codigo"]] = {
        "ine": ine["codigo"], "nombre": ine["NOMBRE"], "ccaa": ccaa, "provincia": ine["provincia"],
        "dias": dias, "parciales": sorted(parciales, key=lambda p: (p["fecha"], p["ambito"])), "fuente": fuente,
    }


for cc in ("AN", "AR", "AS", "IB", "CN", "CB", "CM", "CT", "EX", "GA", "MD", "MC", "NC", "PV", "RI", "VC"):
    for r in cargar(f"{cc}.json"):
        meter(r, cc, cc)
# Castilla y León: listas iniciales y complementarias (estas prevalecen).
for prov, ficheros in {"Ávila": ["CL_avila"], "Burgos": ["CL_burgos"], "León": ["CL_leon", "CL_leon2"],
                       "Palencia": ["CL_palencia"], "Salamanca": ["CL_salamanca", "CL_salamanca2"],
                       "Segovia": ["CL_segovia"], "Soria": ["CL_soria"], "Valladolid": ["CL_valladolid"],
                       "Zamora": ["CL_zamora", "CL_zamora2"]}.items():
    for f in ficheros:
        for r in cargar(f + ".json"):
            r.setdefault("provincia", prov)
            meter(r, "CL", "CL:" + prov)

# Ceuta y Melilla: un solo municipio cada una.
for cod, nombre, cc, dias, fuente in (
    ("51001", "Ceuta", "CE", ["2026-03-20", "2026-06-13"], "CE"),
    ("52001", "Melilla", "ML", ["2026-09-08", "2026-09-17"], "ML"),
):
    todos[cod] = {"ine": cod, "nombre": nombre, "ccaa": cc, "provincia": nombre, "dias": dias, "parciales": [],
                  "fuente": fuente}

# Isla de cada municipio canario (para la fiesta insular del BOE).
ISLAS = {
    "Fuerteventura": ["Antigua", "Betancuria", "Oliva, La", "Pájara", "Puerto del Rosario", "Tuineje"],
    "Lanzarote": ["Arrecife", "Haría", "San Bartolomé", "Teguise", "Tías", "Tinajo", "Yaiza"],
    "La Gomera": ["Agulo", "Alajeró", "Hermigua", "San Sebastián de la Gomera", "Valle Gran Rey", "Vallehermoso"],
    "El Hierro": ["Valverde", "Frontera", "Pinar de El Hierro, El"],
    "La Palma": ["Barlovento", "Breña Alta", "Breña Baja", "Fuencaliente de la Palma", "Garafía",
                 "Llanos de Aridane, Los", "Paso, El", "Puntagorda", "Puntallana", "San Andrés y Sauces",
                 "Santa Cruz de la Palma", "Tazacorte", "Tijarafe", "Villa de Mazo"],
}
canarias = {x["NOMBRE"]: x for x in REG if x["ccaa"] == "CN"}
asignadas = {}
for isla, nombres in ISLAS.items():
    for n in nombres:
        assert n in canarias, n
        asignadas[canarias[n]["codigo"]] = isla
for x in canarias.values():
    asignadas.setdefault(x["codigo"], "Gran Canaria" if x["provincia"] == "Las Palmas" else "Tenerife")
assert Counter(asignadas.values()) == {"Tenerife": 31, "Gran Canaria": 21, "La Palma": 14, "Lanzarote": 7,
                                        "Fuerteventura": 6, "La Gomera": 6, "El Hierro": 3}, Counter(asignadas.values())
for cod, r in todos.items():
    if r["ccaa"] == "CN":
        r["isla"] = asignadas[cod]

# Control: las 50 capitales comprobadas a mano deben coincidir.
for clave, (nombre, cc, isla, dias) in CAP.CAPITALES.items():
    ine = buscar(nombre, cc) or buscar_aprox(nombre, cc, None)
    esperado = sorted(f"2026-{m:02d}-{d:02d}" for m, d in dias)
    got = todos.get(ine["codigo"]) if ine else None
    if not got:
        problemas.append((cc, nombre, "capital sin datos"))
    elif got["dias"] != esperado:
        problemas.append((cc, nombre, f"capital distinta: {got['dias']} ≠ {esperado}"))

por_cc = Counter(r["ccaa"] for r in todos.values())
total_ine = Counter(x["ccaa"] for x in REG)
print("Cobertura por comunidad (municipios con datos / municipios INE):")
for cc in sorted(total_ine):
    print(f"  {cc}: {por_cc.get(cc, 0)}/{total_ine[cc]}")
print("TOTAL:", len(todos), "de", len(REG))
print("Con fiestas por núcleos:", sum(bool(r["parciales"]) for r in todos.values()))
print("Con más de dos días:", [(r["nombre"], r["dias"]) for r in todos.values() if len(r["dias"]) > 2])
print("PROBLEMAS:", problemas)

fuentes = {k: {"texto": t, "url": u} for k, (t, u) in FUENTES.items()}
fuentes.update({f"CL:{p}": {"texto": t, "url": URL_CL} for p, t in FUENTES_CL.items()})
salida = {"anio": 2026, "fuentes": fuentes,
          "municipios": sorted(todos.values(), key=lambda r: r["ine"])}
Path(OUT / "municipios_2026.json").write_text(json.dumps(salida, ensure_ascii=False, separators=(",", ":")),
                                              encoding="utf-8")
print("tamaño:", (OUT / "municipios_2026.json").stat().st_size // 1024, "KB")
