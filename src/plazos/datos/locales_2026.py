"""Fiestas locales de 2026 de las 50 capitales de provincia.

Cada dato se ha tomado del boletín oficial que lo publica (y de sus modificaciones
conocidas hasta el 30-9-2026). Ceuta y Melilla no aparecen aquí porque no son capitales de
provincia; sus fiestas locales (BOCCE y BOME) están en municipios_2026.json, como las de los
demás municipios. Formato: clave -> (nombre, comunidad, isla, días, fuente).
"""

FUENTES = {
    "AN": (
        "BOJA n.º 197, de 14-10-2025 (Resolución de 6-10-2025); modificaciones en BOJA n.º 33 y 79 de 2026",
        "https://www.juntadeandalucia.es/boja/2025/197/28",
    ),
    "AR": (
        "BOA n.º 225, de 20-11-2025 (Resolución de 4-11-2025)",
        "https://www.boa.aragon.es/cgi-bin/EBOA/BRSCGI?CMD=VEROBJ&MLKOB=1421874360606",
    ),
    "AS": (
        "BOPA de 16-6-2025 (Resolución de 3-6-2025)",
        "https://miprincipado.asturias.es/documents/d/guest/2025-04744",
    ),
    "IB": (
        "BOIB n.º 129, de 27-9-2025 (Resolución de 25-9-2025)",
        "https://www.caib.es/sites/calendarilaboral/f/529360",
    ),
    "CN": (
        "BOC n.º 165, de 21-8-2025 (Orden de 6-8-2025)",
        "https://www.gobiernodecanarias.org/boc/2025/165/3029.html",
    ),
    "CB": (
        "BOC n.º 238, de 11-12-2025 (Resolución de 2-12-2025)",
        "https://boc.cantabria.es/boces/verAnuncioAction.do?idAnuBlob=428192",
    ),
    "CL": (
        "BOP de cada provincia (septiembre de 2025); Salamanca, relación complementaria en BOP n.º 234, de 4-12-2025",
        "https://trabajoyprevencion.jcyl.es/web/es/relaciones-laborales/calendario-laboral-2026.html",
    ),
    "CM": (
        "DOCM n.º 240, de 12-12-2025 (Anuncio de 4-12-2025); modificación en DOCM de 16-3-2026",
        "https://docm.jccm.es/docm/descargarArchivo.do?ruta=2025/12/12/pdf/2025_9468.pdf&tipo=rutaDocm",
    ),
    "CT": (
        "DOGC n.º 9565, de 17-12-2025 (Orden EMT/208/2025); modificación por Orden EMT/3/2026",
        "https://dogc.gencat.cat/ca/document-del-dogc/?documentId=1032232",
    ),
    "EX": ("DOE n.º 204, de 23-10-2025", "https://doe.juntaex.es/pdfs/doe/2025/2040o/25063799.pdf"),
    "GA": (
        "DOG n.º 210, de 30-10-2025 (Resolución de 21-10-2025)",
        "https://www.xunta.gal/dog/Publicados/2025/20251030/AnuncioG0767-221025-0001_es.html",
    ),
    "MD": (
        "BOCM n.º 296, de 12-12-2025 (Resolución de 2-12-2025); modificación en BOCM n.º 309",
        "https://www.bocm.es/boletin/CM_Orden_BOCM/2025/12/12/BOCM-20251212-34.PDF",
    ),
    "MC": ("BORM n.º 163, de 17-7-2025", "https://www.borm.es/services/anuncio/ano/2025/numero/3546/pdf?id=837607"),
    "NC": (
        "BON n.º 241, de 2-12-2025 (Resolución 682/2025) y Resolución 390/2025 (3 de diciembre, común a Navarra)",
        "https://bon.navarra.es/",
    ),
    "PV": (
        "BOTHA n.º 82, de 21-7-2025 (Álava); BOB n.º 138 y 148 de 2025 (Bizkaia); BOG n.º 168, de 4-9-2025 (Gipuzkoa)",
        "https://egoitza.gipuzkoa.eus/gao-bog/castell/bog/2025/09/04/c2506163.pdf",
    ),
    "RI": ("BOR n.º 159, de 19-8-2025", "https://web.larioja.org/bor-portada/"),
    "VC": (
        "DOGV n.º 10238, de 14-11-2025 (Resolución de 12-11-2025); modificación en DOGV n.º 10281",
        "https://dogv.gva.es/datos/2025/11/14/pdf/2025_46326_es.pdf",
    ),
}

CAPITALES = {
    # Andalucía
    "almeria": ("Almería", "AN", None, ((6, 24), (8, 29))),
    "cadiz": ("Cádiz", "AN", None, ((2, 16), (10, 7))),
    "cordoba": ("Córdoba", "AN", None, ((9, 8), (10, 24))),
    "granada": ("Granada", "AN", None, ((1, 2), (6, 4))),
    "huelva": ("Huelva", "AN", None, ((8, 3), (9, 8))),
    "jaen": ("Jaén", "AN", None, ((6, 11), (11, 25))),
    "malaga": ("Málaga", "AN", None, ((8, 19), (9, 8))),
    "sevilla": ("Sevilla", "AN", None, ((4, 22), (6, 4))),
    # Aragón
    "huesca": ("Huesca", "AR", None, ((1, 22), (8, 10))),
    "teruel": ("Teruel", "AR", None, ((4, 7), (7, 13))),
    "zaragoza": ("Zaragoza", "AR", None, ((1, 29), (3, 5))),
    # Asturias
    "oviedo": ("Oviedo", "AS", None, ((5, 26), (9, 21))),
    # Illes Balears
    "palma": ("Palma", "IB", None, ((1, 20), (6, 24))),
    # Canarias
    "las palmas de gran canaria": ("Las Palmas de Gran Canaria", "CN", "Gran Canaria", ((2, 17), (6, 24))),
    "santa cruz de tenerife": ("Santa Cruz de Tenerife", "CN", "Tenerife", ((2, 17), (5, 4))),
    # Cantabria
    "santander": ("Santander", "CB", None, ((5, 25), (7, 25))),
    # Castilla y León
    "avila": ("Ávila", "CL", None, ((5, 2), (10, 15))),
    "burgos": ("Burgos", "CL", None, ((6, 12), (6, 29))),
    "leon": ("León", "CL", None, ((6, 24), (10, 5))),
    "palencia": ("Palencia", "CL", None, ((2, 2), (9, 2))),
    "salamanca": ("Salamanca", "CL", None, ((6, 12), (9, 8))),
    "segovia": ("Segovia", "CL", None, ((6, 29), (10, 26))),
    "soria": ("Soria", "CL", None, ((6, 25), (10, 2))),
    "valladolid": ("Valladolid", "CL", None, ((5, 13), (9, 8))),
    "zamora": ("Zamora", "CL", None, ((5, 25), (6, 29))),
    # Castilla-La Mancha
    "albacete": ("Albacete", "CM", None, ((6, 24), (9, 8))),
    "ciudad real": ("Ciudad Real", "CM", None, ((5, 25), (8, 22))),
    "cuenca": ("Cuenca", "CM", None, ((6, 1), (9, 21))),
    "guadalajara": ("Guadalajara", "CM", None, ((9, 8), (9, 18))),
    "toledo": ("Toledo", "CM", None, ((1, 23), (11, 26))),
    # Cataluña
    "barcelona": ("Barcelona", "CT", None, ((5, 25), (9, 24))),
    "girona": ("Girona", "CT", None, ((7, 25), (10, 29))),
    "lleida": ("Lleida", "CT", None, ((5, 11), (9, 29))),
    "tarragona": ("Tarragona", "CT", None, ((8, 19), (9, 23))),
    # Extremadura
    "badajoz": ("Badajoz", "EX", None, ((2, 17), (6, 24))),
    "caceres": ("Cáceres", "EX", None, ((4, 23), (5, 29))),
    # Galicia
    "a coruna": ("A Coruña", "GA", None, ((2, 17), (10, 7))),
    "lugo": ("Lugo", "GA", None, ((2, 17), (10, 5))),
    "ourense": ("Ourense", "GA", None, ((2, 17), (11, 11))),
    "pontevedra": ("Pontevedra", "GA", None, ((2, 18), (7, 11))),
    # Comunidad de Madrid
    "madrid": ("Madrid", "MD", None, ((5, 15), (11, 9))),
    # Región de Murcia
    "murcia": ("Murcia", "MC", None, ((4, 7), (9, 15))),
    # Navarra: el 3 de diciembre es fiesta local común a toda la Comunidad Foral.
    "pamplona": ("Pamplona", "NC", None, ((11, 30), (12, 3))),
    # País Vasco: cada territorio tiene un día común (28-4 Álava, 31-7 Bizkaia y Gipuzkoa).
    "vitoria-gasteiz": ("Vitoria-Gasteiz", "PV", None, ((4, 28), (8, 5))),
    "bilbao": ("Bilbao", "PV", None, ((7, 31), (8, 28))),
    "donostia / san sebastian": ("Donostia / San Sebastián", "PV", None, ((1, 20), (7, 31))),
    # La Rioja
    "logrono": ("Logroño", "RI", None, ((6, 11), (9, 21))),
    # Comunitat Valenciana
    "alicante": ("Alicante", "VC", None, ((4, 16), (6, 23))),
    "castellon de la plana": ("Castellón de la Plana", "VC", None, ((3, 9), (6, 29))),
    "valencia": ("València", "VC", None, ((1, 22), (4, 13))),
}

ALIAS = {
    "coruna": "a coruna",
    "la coruna": "a coruna",
    "palma de mallorca": "palma",
    "las palmas": "las palmas de gran canaria",
    "gerona": "girona",
    "lerida": "lleida",
    "orense": "ourense",
    "vitoria": "vitoria-gasteiz",
    "gasteiz": "vitoria-gasteiz",
    "donostia": "donostia / san sebastian",
    "san sebastian": "donostia / san sebastian",
    "donostia-san sebastian": "donostia / san sebastian",
    "iruna": "pamplona",
    "pamplona/iruna": "pamplona",
    "pamplona / iruna": "pamplona",
    "alacant": "alicante",
    "castellon": "castellon de la plana",
    "castello": "castellon de la plana",
    "castello de la plana": "castellon de la plana",
}
