"""Días inhábiles de 2026 de ámbito nacional y autonómico.

Fuente: Resolución de 18 de noviembre de 2025, de la Secretaría de Estado de Función
Pública (BOE-A-2025-23702), anexo. Sábados y domingos no se listan: son inhábiles siempre.
"""

REFERENCIA = "BOE-A-2025-23702"
URL = "https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-23702"

TODAS = (
    "AN",
    "AR",
    "AS",
    "IB",
    "CN",
    "CB",
    "CL",
    "CM",
    "CT",
    "EX",
    "GA",
    "MD",
    "MC",
    "NC",
    "PV",
    "RI",
    "VC",
    "CE",
    "ML",
)

# (mes, día): "ES" si es inhábil en todo el territorio, o tupla de comunidades.
DIAS = {
    (1, 1): "ES",
    (1, 6): "ES",
    (3, 2): ("IB",),
    (3, 19): ("GA", "MC", "PV", "VC", "NC"),
    (3, 20): ("ML",),
    (4, 2): ("AN", "AR", "AS", "IB", "CN", "CB", "CM", "EX", "GA", "MC", "PV", "RI", "CL", "MD", "NC", "CE", "ML"),
    (4, 3): "ES",
    (4, 6): ("IB", "CM", "CT", "PV", "RI", "NC", "VC"),
    (4, 23): ("AR", "CL"),
    (5, 1): "ES",
    (5, 27): ("CE", "ML"),
    (6, 4): ("CM",),
    (6, 9): ("RI", "MC"),
    (6, 24): ("CT", "GA", "VC"),
    (7, 28): ("CB",),
    (8, 5): ("CE",),
    (9, 2): ("CE",),
    (9, 8): ("AS", "EX"),
    (9, 11): ("CT",),
    (9, 15): ("CB",),
    (10, 9): ("VC",),
    (10, 12): "ES",
    (11, 2): ("AN", "AR", "AS", "CN", "CM", "EX", "CL", "MD", "NC"),
    (12, 7): ("AN", "AR", "AS", "CB", "EX", "MC", "RI", "CL", "MD", "ML"),
    (12, 8): "ES",
    (12, 25): "ES",
}

# Nota 1 del anexo (Decreto 61/2025, BOC 5-5-2025): fiestas insulares de Canarias.
INSULARES_CANARIAS = {
    "El Hierro": (9, 24),
    "Fuerteventura": (9, 18),
    "Gran Canaria": (9, 8),
    "La Gomera": (10, 5),
    "La Palma": (8, 5),
    "Lanzarote": (9, 15),
    "La Graciosa": (9, 15),
    "Tenerife": (2, 2),
}
