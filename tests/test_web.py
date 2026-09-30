"""La herramienta web (web/plazos.js) debe dar exactamente lo mismo que la librería."""

import json
import random
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

from plazos import calcular, municipios

WEB = Path(__file__).resolve().parents[1] / "web"
NODE = shutil.which("node")

EJECUTOR = """
const fs = require("fs");
require(process.argv[2]);
globalThis.PLAZOS_MUNICIPIOS = JSON.parse(fs.readFileSync(process.argv[4], "utf8"));
const Plazos = require(process.argv[3]);
const casos = JSON.parse(fs.readFileSync(0, "utf8"));
const salida = casos.map((c) => {
  try {
    const r = Plazos.calcular(c);
    return {
      vencimiento: Plazos.iso(r.vencimiento),
      presentacion: r.presentacionHasta,
      excluidos: r.excluidos.map((e) => [Plazos.iso(e.fecha), e.motivo]),
      pasos: r.pasos.map((p) => [p.texto, p.norma ? p.norma.cita : null]),
      avisos: r.advertencias,
    };
  } catch (e) { return { error: true }; }
});
process.stdout.write(JSON.stringify(salida));
"""


def _casos(n: int) -> list[dict]:
    azar = random.Random(20260930)
    codigos = sorted(m.ine for m in municipios.todos(2026))
    casos = []
    for _ in range(n):
        j = azar.choice(["administrativo", "civil", "contencioso", "social"])
        u = azar.choice(
            ["dias", "dias", "dias", "meses", "anios"] + (["dias_naturales"] if j == "administrativo" else [])
        )
        caso = {
            "inicio": (date(2025, 11, 1) + timedelta(days=azar.randrange(420))).isoformat(),
            "cantidad": azar.choice([1, 2, 3, 5, 10, 15, 20, 30]) if u.startswith("dias") else azar.choice([1, 2, 3]),
            "unidad": u,
            "jurisdiccion": j,
            "urgente": j != "administrativo" and azar.random() < 0.2,
        }
        eleccion = azar.random()
        if eleccion < 0.5:
            caso["municipio"] = azar.choice(codigos)
        elif eleccion < 0.8:
            caso["ccaa"] = azar.choice(["AN", "CT", "MD", "PV", "VC", "CN", "NC", "GA"])
            if azar.random() < 0.5:
                caso["festivosLocales"] = [(date(2026, 1, 1) + timedelta(days=azar.randrange(365))).isoformat()]
        if j == "administrativo" and azar.random() < 0.2:
            caso["lugares"] = [{"ccaa": azar.choice(["MD", "VC", "AN"])}]
        casos.append(caso)
    return casos


def _python(c: dict) -> dict:
    from plazos import Lugar

    r = calcular(
        date.fromisoformat(c["inicio"]),
        c["cantidad"],
        c["unidad"],
        c["jurisdiccion"],
        ccaa=c.get("ccaa"),
        festivos_locales=[date.fromisoformat(f) for f in c.get("festivosLocales", [])],
        municipio=c.get("municipio"),
        lugares=[Lugar(**lugar) for lugar in c.get("lugares", [])],
        urgente=c["urgente"],
    )
    return {
        "vencimiento": r.vencimiento.isoformat(),
        "presentacion": r.presentacion_hasta.strftime("%Y-%m-%dT%H:%M") if r.presentacion_hasta else None,
        "excluidos": [[e.fecha.isoformat(), e.motivo] for e in r.excluidos],
        "pasos": [[p.texto, p.norma.cita if p.norma else None] for p in r.pasos],
        "avisos": list(r.advertencias),
    }


def _exportador():
    import importlib.util

    ruta = Path(__file__).resolve().parents[1] / "scripts" / "exportar_web.py"
    spec = importlib.util.spec_from_file_location("exportar_web", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.mark.skipif(NODE is None, reason="hace falta Node.js")
def test_web_coincide_con_python(tmp_path):
    # Los datos se generan con la versión de holidays instalada, para comparar solo el motor.
    datos = tmp_path / "datos.js"
    _exportador().main(datos)
    casos = _casos(600)
    script = tmp_path / "ejecutar.js"
    script.write_text(EJECUTOR, encoding="utf-8")
    salida = subprocess.run(
        [NODE, str(script), str(datos), str(WEB / "plazos.js"), str(datos.with_name("municipios.json"))],
        input=json.dumps(casos),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    web = json.loads(salida.stdout)
    for caso, resultado in zip(casos, web, strict=True):
        assert resultado == _python(caso), caso


def test_datos_web_al_dia(tmp_path):
    """web/datos.js debe regenerarse cuando cambian los calendarios (scripts/exportar_web.py)."""
    import holidays

    actual = (WEB / "datos.js").read_text(encoding="utf-8")
    if f'"holidays":"{holidays.__version__}"' not in actual:
        pytest.skip("web/datos.js se generó con otra versión de holidays")
    nuevo = tmp_path / "datos.js"
    _exportador().main(nuevo)
    assert nuevo.read_text(encoding="utf-8") == actual, "ejecuta scripts/exportar_web.py"
