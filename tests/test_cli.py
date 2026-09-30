import json

import pytest

from plazos.cli import main


def test_cli_texto(capsys):
    assert main(["2026-07-20", "20", "dias", "-j", "civil", "--ccaa", "MD"]) == 0
    out = capsys.readouterr().out
    assert "martes, 15 de septiembre de 2026" in out


def test_cli_json(capsys):
    main(["2026-05-14", "1", "--ccaa", "MD", "--local", "2026-05-15", "--json"])
    datos = json.loads(capsys.readouterr().out)
    assert datos["vencimiento"] == "2026-05-18"
    assert datos["normas"][0]["url"].startswith("https://www.boe.es/")


def test_cli_error(capsys):
    with pytest.raises(SystemExit):
        main(["2026-13-01", "5"])


def test_cli_pago(capsys):
    assert main(["2026-07-16", "--pago", "voluntario"]) == 0
    assert "lunes, 7 de septiembre de 2026" in capsys.readouterr().out


def test_cli_horas(capsys):
    assert main(["2026-10-09", "24", "horas", "--hora", "10:00", "--ccaa", "MD"]) == 0
    assert "a las 10:00" in capsys.readouterr().out


def test_cli_sin_cantidad(capsys):
    with pytest.raises(SystemExit):
        main(["2026-07-16"])
