"""Implementa: RF-R1-16."""

import pytest


def _login(client, make_user, *, role: str = "admin", username: str = "gonzalo") -> str:
    password = "una-contraseña-larga-123"
    make_user(username=username, password=password, role=role)
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.cookies["csrf_token"]


@pytest.mark.spec("RF-R1-16")
def test_crear_tema_sin_sesion_devuelve_401(client) -> None:
    response = client.post("/api/admin/topics", json={"name": "Asia", "slug": "asia"})
    assert response.status_code == 401


@pytest.mark.spec("RF-R1-16")
@pytest.mark.spec("RF-R1-07")
def test_crear_tema_sin_rol_admin_devuelve_403(client, make_user) -> None:
    csrf = _login(client, make_user, role="lector")

    response = client.post(
        "/api/admin/topics",
        json={"name": "Asia", "slug": "asia"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 403


@pytest.mark.spec("RF-R1-16")
def test_crear_tema_sin_csrf_devuelve_403(client, make_user) -> None:
    _login(client, make_user)

    response = client.post("/api/admin/topics", json={"name": "Asia", "slug": "asia"})

    assert response.status_code == 403


@pytest.mark.spec("RF-R1-16")
def test_crear_tema(client, make_user) -> None:
    csrf = _login(client, make_user)

    response = client.post(
        "/api/admin/topics",
        json={"name": "Asia", "slug": "asia", "description": "Viajes por Asia", "color": "#ff0000"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Asia"
    assert body["slug"] == "asia"
    assert body["description"] == "Viajes por Asia"
    assert body["color"] == "#ff0000"


@pytest.mark.spec("RF-R1-16")
def test_crear_tema_con_slug_duplicado_devuelve_409(client, make_user) -> None:
    csrf = _login(client, make_user)
    client.post("/api/admin/topics", json={"name": "Asia", "slug": "asia"}, headers={"X-CSRF-Token": csrf})

    response = client.post(
        "/api/admin/topics", json={"name": "Asia 2", "slug": "asia"}, headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 409


@pytest.mark.spec("RF-R1-16")
def test_listar_y_obtener_tema(client, make_user, make_topic) -> None:
    _login(client, make_user)
    topic = make_topic(name="Europa", slug="europa")

    list_response = client.get("/api/admin/topics")
    assert list_response.status_code == 200
    assert any(t["id"] == str(topic.id) for t in list_response.json())

    get_response = client.get(f"/api/admin/topics/{topic.id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Europa"


@pytest.mark.spec("RF-R1-16")
def test_obtener_tema_inexistente_devuelve_404(client, make_user) -> None:
    _login(client, make_user)

    response = client.get("/api/admin/topics/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


@pytest.mark.spec("RF-R1-16")
def test_actualizar_tema(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic(name="Europa", slug="europa")

    response = client.put(
        f"/api/admin/topics/{topic.id}",
        json={"description": "Nueva descripción"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Nueva descripción"
    assert body["name"] == "Europa"


@pytest.mark.spec("RF-R1-16")
def test_actualizar_tema_con_slug_duplicado_devuelve_409(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    make_topic(name="Europa", slug="europa")
    other = make_topic(name="Asia", slug="asia")

    response = client.put(
        f"/api/admin/topics/{other.id}", json={"slug": "europa"}, headers={"X-CSRF-Token": csrf}
    )

    assert response.status_code == 409


@pytest.mark.spec("RF-R1-16")
def test_borrar_tema(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic(name="Europa", slug="europa")

    response = client.delete(f"/api/admin/topics/{topic.id}", headers={"X-CSRF-Token": csrf})

    assert response.status_code == 204
    assert client.get(f"/api/admin/topics/{topic.id}").status_code == 404


@pytest.mark.spec("RF-R1-16")
def test_borrar_tema_referenciado_por_un_viaje_devuelve_409(client, make_user, make_topic, make_trip) -> None:
    csrf = _login(client, make_user)
    topic = make_topic(name="Europa", slug="europa")
    make_trip(topic=topic)

    response = client.delete(f"/api/admin/topics/{topic.id}", headers={"X-CSRF-Token": csrf})

    assert response.status_code == 409
