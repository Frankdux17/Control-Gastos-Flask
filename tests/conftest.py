import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    """App de pruebas con una base de datos temporal (nunca la base real)."""
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "pruebas",
        "DATABASE": str(tmp_path / "test.db"),
    })
    yield app


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_logueado(client):
    """Cliente que ya inició sesión como admin."""
    client.post("/login", data={"usuario": "admin", "clave": "123"})
    return client


@pytest.fixture
def registrar(client_logueado):
    """Atajo para registrar un gasto desde las pruebas."""
    def _registrar(fecha, descripcion, monto):
        return client_logueado.post(
            "/gastos",
            data={"fecha": fecha, "descripcion": descripcion, "monto": monto},
            follow_redirects=True,
        )
    return _registrar
