import pytest

from utils import formatear_monto, validar_gasto


def test_gasto_valido():
    assert validar_gasto("2026-11-10", "Almuerzo", "15.50") == []


@pytest.mark.parametrize("fecha", ["", "10/11/2026", "2026-13-01", "2026-02-30", None])
def test_fecha_invalida(fecha):
    assert "La fecha no es válida." in validar_gasto(fecha, "Pasaje", "2")


@pytest.mark.parametrize("descripcion", ["", "   ", None])
def test_descripcion_vacia(descripcion):
    assert "La descripción es obligatoria." in validar_gasto("2026-11-10", descripcion, "2")


@pytest.mark.parametrize("descripcion, esperado_valido", [
    ("a" * 99, True),    # límite - 1
    ("a" * 100, True),   # límite exacto
    ("a" * 101, False),  # límite + 1
])
def test_descripcion_valores_limite(descripcion, esperado_valido):
    errores = validar_gasto("2026-11-10", descripcion, "5")
    assert (errores == []) == esperado_valido


@pytest.mark.parametrize("monto, esperado_valido", [
    ("0.01", True),
    ("100", True),
    ("0", False),
    ("-5", False),
    ("abc", False),
    ("", False),
    ("nan", False),
    ("inf", False),
    (None, False),
])
def test_monto(monto, esperado_valido):
    errores = validar_gasto("2026-11-10", "Gasto", monto)
    assert (errores == []) == esperado_valido


def test_varios_errores_a_la_vez():
    assert len(validar_gasto("", "", "-1")) == 3


@pytest.mark.parametrize("monto, texto", [
    (0, "S/ 0.00"),
    (15.5, "S/ 15.50"),
    (1234.567, "S/ 1,234.57"),
])
def test_formatear_monto(monto, texto):
    assert formatear_monto(monto) == texto
