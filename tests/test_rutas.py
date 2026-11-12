"""Pruebas de rutas con el cliente de pruebas de Flask."""


# ---------- Acceso ----------
def test_inicio_sin_sesion_redirige_a_login(client):
    r = client.get("/")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_pagina_login_carga(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert b"Iniciar sesi" in r.data


def test_login_correcto(client):  # CP-01
    r = client.post("/login", data={"usuario": "admin", "clave": "123"})
    assert r.status_code == 302
    assert "/gastos" in r.headers["Location"]


def test_login_clave_incorrecta(client):  # CP-02
    r = client.post("/login", data={"usuario": "admin", "clave": "999"},
                    follow_redirects=True)
    assert b"Credenciales inv" in r.data


def test_login_usuario_incorrecto(client):
    r = client.post("/login", data={"usuario": "otro", "clave": "123"})
    assert b"Credenciales inv" in r.data


def test_gastos_sin_sesion(client):  # CP-03
    r = client.get("/gastos")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_reporte_sin_sesion(client):
    r = client.get("/reporte", follow_redirects=True)
    assert b"Inicia sesi" in r.data


def test_logout_cierra_sesion(client_logueado):
    client_logueado.get("/logout")
    r = client_logueado.get("/gastos")
    assert r.status_code == 302


# ---------- Registro de gastos ----------
def test_lista_vacia(client_logueado):
    r = client_logueado.get("/gastos")
    assert r.status_code == 200
    assert b"no hay gastos" in r.data


def test_registrar_gasto(registrar):  # CP-04
    r = registrar("2026-11-10", "Almuerzo menu", "15.50")
    assert b"Gasto registrado" in r.data
    assert b"Almuerzo menu" in r.data
    assert b"S/ 15.50" in r.data


def test_registrar_monto_invalido_no_guarda(registrar, client_logueado):  # CP-05
    r = registrar("2026-11-10", "Pasaje", "abc")
    assert b"El monto debe ser" in r.data
    assert b"<td>Pasaje</td>" not in r.data


def test_registrar_descripcion_vacia(registrar):
    r = registrar("2026-11-10", "   ", "10")
    assert b"La descripci" in r.data


def test_eliminar_gasto(registrar, client_logueado):  # CP-06
    registrar("2026-11-10", "Cafe", "5")
    r = client_logueado.post("/gastos/1/eliminar", follow_redirects=True)
    assert b"Gasto eliminado" in r.data
    assert b"<td>Cafe</td>" not in r.data


def test_eliminar_gasto_inexistente(client_logueado):
    r = client_logueado.post("/gastos/999/eliminar", follow_redirects=True)
    assert b"El gasto no existe" in r.data


# ---------- Reporte ----------
def test_reporte_total(registrar, client_logueado):  # CP-07
    registrar("2026-10-05", "Luz", "80")
    registrar("2026-11-02", "Agua", "20.50")
    r = client_logueado.get("/reporte")
    assert r.status_code == 200
    assert b"S/ 100.50" in r.data
    assert b"2026-10" in r.data and b"2026-11" in r.data


def test_reporte_filtrado_por_fechas(registrar, client_logueado):  # CP-08
    registrar("2026-10-05", "Luz", "80")
    registrar("2026-11-02", "Agua", "20")
    r = client_logueado.get("/reporte?desde=2026-11-01&hasta=2026-11-30")
    assert b"<td>Agua</td>" in r.data
    assert b"<td>Luz</td>" not in r.data
    assert b"S/ 20.00" in r.data


def test_reporte_csv(registrar, client_logueado):
    registrar("2026-11-02", "Agua", "20")
    r = client_logueado.get("/reporte/csv")
    assert r.status_code == 200
    assert r.mimetype == "text/csv"
    assert "Agua" in r.get_data(as_text=True)


def test_ruta_inexistente(client):
    r = client.get("/no-existe")
    assert r.status_code == 404
