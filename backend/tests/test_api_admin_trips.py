"""Implementa: RF-R1-15, RF-R1-18."""

import pytest


def _login(client, make_user, *, role: str = "admin", username: str = "gonzalo") -> str:
    password = "una-contraseña-larga-123"
    make_user(username=username, password=password, role=role)
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.cookies["csrf_token"]


@pytest.mark.spec("RF-R1-15")
def test_crear_viaje_sin_sesion_devuelve_401(client, make_topic) -> None:
    topic = make_topic()
    response = client.post("/api/admin/trips", json={"title": "Japón", "topic_id": str(topic.id)})
    assert response.status_code == 401


@pytest.mark.spec("RF-R1-15")
@pytest.mark.spec("RF-R1-07")
def test_crear_viaje_sin_rol_admin_devuelve_403(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user, role="lector")
    topic = make_topic()

    response = client.post(
        "/api/admin/trips",
        json={"title": "Japón", "topic_id": str(topic.id)},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 403


@pytest.mark.spec("RF-R1-15")
def test_crear_viaje_empieza_en_borrador_con_slug_autogenerado(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic()

    response = client.post(
        "/api/admin/trips",
        json={"title": "Un Viaje a Japón!", "topic_id": str(topic.id)},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "draft"
    assert body["slug"] == "un-viaje-a-japon"


@pytest.mark.spec("RF-R1-15")
def test_crear_viaje_con_titulo_repetido_genera_slug_sin_colision(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic()
    payload = {"title": "Japón", "topic_id": str(topic.id)}

    first = client.post("/api/admin/trips", json=payload, headers={"X-CSRF-Token": csrf})
    second = client.post("/api/admin/trips", json=payload, headers={"X-CSRF-Token": csrf})

    assert first.json()["slug"] == "japon"
    assert second.json()["slug"] == "japon-2"


@pytest.mark.spec("RF-R1-15")
def test_crear_viaje_con_tema_inexistente_devuelve_400(client, make_user) -> None:
    csrf = _login(client, make_user)

    response = client.post(
        "/api/admin/trips",
        json={"title": "Japón", "topic_id": "00000000-0000-0000-0000-000000000000"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 400


@pytest.mark.spec("RF-R1-15")
def test_crear_viaje_con_etiquetas(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic()

    response = client.post(
        "/api/admin/trips",
        json={"title": "Japón", "topic_id": str(topic.id), "tag_names": ["montaña", "comida", "montaña"]},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.json()["tags"] == ["comida", "montaña"]


@pytest.mark.spec("RF-R1-18")
def test_crear_viaje_con_content_json_rellena_content_html_sanitizado(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic()
    content_json = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Hola"},
                    {"type": "text", "text": "<script>alert(1)</script>"},
                ],
            }
        ],
    }

    response = client.post(
        "/api/admin/trips",
        json={"title": "Japón", "topic_id": str(topic.id), "content_json": content_json},
        headers={"X-CSRF-Token": csrf},
    )

    body = response.json()
    assert body["content_html"] == "<p>Hola&lt;script&gt;alert(1)&lt;/script&gt;</p>"
    assert "<script>" not in body["content_html"]


@pytest.mark.spec("RF-R1-15")
def test_crear_viaje_con_foto_de_portada_inexistente_devuelve_400(client, make_user, make_topic) -> None:
    csrf = _login(client, make_user)
    topic = make_topic()

    response = client.post(
        "/api/admin/trips",
        json={
            "title": "Japón",
            "topic_id": str(topic.id),
            "cover_photo_id": "00000000-0000-0000-0000-000000000000",
        },
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 400


@pytest.mark.spec("RF-R1-15")
def test_actualizar_etiquetas_de_un_viaje(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.put(
        f"/api/admin/trips/{trip.id}",
        json={"tag_names": ["playa", "sol"]},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.json()["tags"] == ["playa", "sol"]


@pytest.mark.spec("RF-R1-18")
def test_actualizar_content_json_de_un_viaje_regenera_content_html(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()
    content_json = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Nuevo"}]}]}

    response = client.put(
        f"/api/admin/trips/{trip.id}",
        json={"content_json": content_json},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.json()["content_html"] == "<p>Nuevo</p>"


@pytest.mark.spec("RF-R1-15")
def test_listar_y_obtener_viaje(client, make_user, make_trip) -> None:
    _login(client, make_user)
    trip = make_trip()

    list_response = client.get("/api/admin/trips")
    assert list_response.status_code == 200
    assert any(t["id"] == str(trip.id) for t in list_response.json())

    get_response = client.get(f"/api/admin/trips/{trip.id}")
    assert get_response.status_code == 200


@pytest.mark.spec("RF-R1-15")
def test_listar_viajes_incluye_borradores(client, make_user, make_trip) -> None:
    from app.models.trip import TripStatus

    _login(client, make_user)
    make_trip(slug="borrador", status=TripStatus.DRAFT)

    response = client.get("/api/admin/trips")

    assert any(t["slug"] == "borrador" for t in response.json())


@pytest.mark.spec("RF-R1-15")
def test_publicar_y_despublicar_viaje(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    publish_response = client.put(
        f"/api/admin/trips/{trip.id}", json={"status": "published"}, headers={"X-CSRF-Token": csrf}
    )
    assert publish_response.json()["status"] == "published"

    unpublish_response = client.put(
        f"/api/admin/trips/{trip.id}", json={"status": "draft"}, headers={"X-CSRF-Token": csrf}
    )
    assert unpublish_response.json()["status"] == "draft"


@pytest.mark.spec("RF-R1-15")
def test_actualizar_viaje_con_tema_inexistente_devuelve_400(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.put(
        f"/api/admin/trips/{trip.id}",
        json={"topic_id": "00000000-0000-0000-0000-000000000000"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 400


@pytest.mark.spec("RF-R1-15")
def test_actualizar_viaje_con_foto_de_portada_inexistente_devuelve_400(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.put(
        f"/api/admin/trips/{trip.id}",
        json={"cover_photo_id": "00000000-0000-0000-0000-000000000000"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 400


@pytest.mark.spec("RF-R1-15")
def test_actualizar_viaje_con_foto_de_portada_valida(client, make_user, make_trip, make_photo) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()
    photo = make_photo(trip=trip)

    response = client.put(
        f"/api/admin/trips/{trip.id}",
        json={"cover_photo_id": str(photo.id)},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 200
    assert response.json()["cover_photo_id"] == str(photo.id)


@pytest.mark.spec("RF-R1-15")
def test_actualizar_viaje_inexistente_devuelve_404(client, make_user) -> None:
    csrf = _login(client, make_user)

    response = client.put(
        "/api/admin/trips/00000000-0000-0000-0000-000000000000",
        json={"title": "Nuevo título"},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 404


@pytest.mark.spec("RF-R1-15")
def test_borrar_viaje(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.delete(f"/api/admin/trips/{trip.id}", headers={"X-CSRF-Token": csrf})

    assert response.status_code == 204
    assert client.get(f"/api/admin/trips/{trip.id}").status_code == 404


@pytest.mark.spec("RF-R1-15")
def test_borrar_viaje_sin_csrf_devuelve_403(client, make_user, make_trip) -> None:
    _login(client, make_user)
    trip = make_trip()

    response = client.delete(f"/api/admin/trips/{trip.id}")

    assert response.status_code == 403
