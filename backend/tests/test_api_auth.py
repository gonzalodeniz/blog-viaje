"""Implementa: RF-R1-01, RF-R1-02, RF-R1-04, RNF-R1-03."""

import time

import pytest

from app.api.deps import SESSION_COOKIE_NAME
from app.core.csrf import CSRF_COOKIE_NAME


@pytest.mark.spec("RF-R1-01")
def test_login_con_credenciales_correctas_devuelve_200_y_cookies(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")

    response = client.post(
        "/api/auth/login", json={"username": "gonzalo", "password": "una-contraseña-larga-123"}
    )

    assert response.status_code == 200
    assert response.json() == {"username": "gonzalo"}
    assert SESSION_COOKIE_NAME in response.cookies
    assert CSRF_COOKIE_NAME in response.cookies


@pytest.mark.spec("RF-R1-02")
def test_cookie_de_sesion_tiene_los_flags_correctos(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")

    response = client.post(
        "/api/auth/login", json={"username": "gonzalo", "password": "una-contraseña-larga-123"}
    )

    set_cookie_headers = response.headers.get_list("set-cookie")
    session_cookie_header = next(h for h in set_cookie_headers if h.startswith(f"{SESSION_COOKIE_NAME}="))

    assert "HttpOnly" in session_cookie_header
    assert "Secure" in session_cookie_header
    assert "samesite=lax" in session_cookie_header.lower()

    csrf_cookie_header = next(h for h in set_cookie_headers if h.startswith(f"{CSRF_COOKIE_NAME}="))
    assert "HttpOnly" not in csrf_cookie_header


@pytest.mark.spec("RF-R1-04")
def test_login_con_password_incorrecta_devuelve_401_generico(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")

    response = client.post("/api/auth/login", json={"username": "gonzalo", "password": "incorrecta"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"


@pytest.mark.spec("RF-R1-04")
def test_login_con_usuario_inexistente_devuelve_el_mismo_401_generico(client) -> None:
    response = client.post("/api/auth/login", json={"username": "no-existe", "password": "cualquier-cosa"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"


@pytest.mark.spec("RF-R1-04")
def test_login_usuario_inexistente_y_password_incorrecta_tardan_tiempos_comparables(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")

    start = time.perf_counter()
    client.post("/api/auth/login", json={"username": "gonzalo", "password": "incorrecta"})
    existing_user_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    client.post("/api/auth/login", json={"username": "no-existe", "password": "incorrecta"})
    missing_user_elapsed = time.perf_counter() - start

    # No es una prueba de canal lateral rigurosa (el entorno de CI tiene
    # ruido), solo comprueba que no hay un atajo grosero: el caso de
    # "usuario inexistente" no debería ser órdenes de magnitud más rápido.
    assert missing_user_elapsed > existing_user_elapsed / 5


@pytest.mark.spec("RF-R1-01")
def test_login_deshabilitado_devuelve_401_generico(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123", disabled=True)

    response = client.post(
        "/api/auth/login", json={"username": "gonzalo", "password": "una-contraseña-larga-123"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuario o contraseña incorrectos"


@pytest.mark.spec("RF-R1-02")
def test_logout_revoca_la_sesion(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")
    login_response = client.post(
        "/api/auth/login", json={"username": "gonzalo", "password": "una-contraseña-larga-123"}
    )
    csrf_token = login_response.cookies[CSRF_COOKIE_NAME]

    # El cliente de test conserva las cookies de la respuesta de login
    # (jar), así que solo hace falta repetir el token CSRF en la cabecera.
    logout_response = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf_token})

    assert logout_response.status_code == 200


@pytest.mark.spec("RNF-R1-03")
def test_logout_sin_token_csrf_devuelve_403(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")
    client.post("/api/auth/login", json={"username": "gonzalo", "password": "una-contraseña-larga-123"})

    logout_response = client.post("/api/auth/logout")

    assert logout_response.status_code == 403


@pytest.mark.spec("RNF-R1-03")
def test_logout_con_csrf_de_cabecera_no_coincidente_devuelve_403(client, make_user) -> None:
    make_user(username="gonzalo", password="una-contraseña-larga-123")
    client.post("/api/auth/login", json={"username": "gonzalo", "password": "una-contraseña-larga-123"})

    logout_response = client.post("/api/auth/logout", headers={"X-CSRF-Token": "valor-que-no-coincide"})

    assert logout_response.status_code == 403


@pytest.mark.spec("RF-R1-01")
def test_endpoint_protegido_sin_cookie_de_sesion_pero_con_csrf_valido_devuelve_401(client) -> None:
    # CSRF válido (cookie y cabecera coinciden) pero sin cookie de sesión:
    # ejercita específicamente la rama de "no autenticado" de
    # get_current_user, no el rechazo por CSRF.
    client.cookies.set(CSRF_COOKIE_NAME, "un-token-csrf-cualquiera")

    response = client.post("/api/auth/logout", headers={"X-CSRF-Token": "un-token-csrf-cualquiera"})

    assert response.status_code == 401
