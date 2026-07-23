"""Implementa: RF-R1-13, RF-R1-14."""

from datetime import date

import pytest

from app.models.trip import TripStatus


def _login(client, make_user, **user_kwargs) -> None:
    username = user_kwargs.pop("username", "gonzalo")
    password = user_kwargs.pop("password", "una-contraseña-larga-123")
    make_user(username=username, password=password, **user_kwargs)
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200


@pytest.mark.spec("RF-R1-01")
def test_listado_sin_sesion_devuelve_401(client) -> None:
    response = client.get("/api/trips")

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado"}


@pytest.mark.spec("RF-R1-01")
def test_articulo_sin_sesion_devuelve_401(client, make_trip) -> None:
    trip = make_trip(slug="mi-viaje", status=TripStatus.PUBLISHED)

    response = client.get(f"/api/trips/{trip.slug}")

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado"}


@pytest.mark.spec("RF-R1-13")
def test_listado_solo_incluye_viajes_publicados(client, make_user, make_topic, make_trip) -> None:
    _login(client, make_user)
    topic = make_topic()
    make_trip(topic=topic, slug="publicado", status=TripStatus.PUBLISHED)
    make_trip(topic=topic, slug="borrador", status=TripStatus.DRAFT)

    response = client.get("/api/trips")

    assert response.status_code == 200
    slugs = [item["slug"] for item in response.json()]
    assert slugs == ["publicado"]


@pytest.mark.spec("RF-R1-13")
def test_listado_ordenado_cronologicamente(client, make_user, make_topic, make_trip) -> None:
    _login(client, make_user)
    topic = make_topic()
    make_trip(topic=topic, slug="viejo", status=TripStatus.PUBLISHED, trip_start=date(2020, 1, 1))
    make_trip(topic=topic, slug="reciente", status=TripStatus.PUBLISHED, trip_start=date(2024, 6, 1))
    make_trip(topic=topic, slug="sin-fecha", status=TripStatus.PUBLISHED, trip_start=None)

    response = client.get("/api/trips")

    slugs = [item["slug"] for item in response.json()]
    assert slugs == ["reciente", "viejo", "sin-fecha"]


@pytest.mark.spec("RF-R1-13")
def test_listado_incluye_los_campos_de_portada(client, make_user, make_topic, make_trip) -> None:
    _login(client, make_user)
    topic = make_topic(name="Asia", slug="asia")
    make_trip(
        topic=topic,
        slug="japon",
        title="Japón",
        excerpt="Dos semanas en Japón",
        status=TripStatus.PUBLISHED,
        trip_start=date(2024, 3, 1),
        trip_end=date(2024, 3, 15),
    )

    response = client.get("/api/trips")

    [item] = response.json()
    assert item["title"] == "Japón"
    assert item["excerpt"] == "Dos semanas en Japón"
    assert item["topic"] == {"id": str(topic.id), "name": "Asia", "slug": "asia"}
    assert item["trip_start"] == "2024-03-01"
    assert item["trip_end"] == "2024-03-15"


@pytest.mark.spec("RF-R1-14")
def test_articulo_devuelve_contenido_y_fotos_publicas_y_privadas(
    client, make_user, make_trip, make_photo
) -> None:
    _login(client, make_user)
    trip = make_trip(
        slug="mi-viaje",
        status=TripStatus.PUBLISHED,
        content_html="<p>Hola mundo</p>",
        place="Kioto",
    )
    make_photo(trip=trip, content_hash="a", visibility="public", caption="Foto pública")
    make_photo(trip=trip, content_hash="b", visibility="private", caption="Foto privada")

    response = client.get(f"/api/trips/{trip.slug}")

    assert response.status_code == 200
    body = response.json()
    assert body["content_html"] == "<p>Hola mundo</p>"
    assert body["place"] == "Kioto"
    captions = {photo["caption"] for photo in body["photos"]}
    assert captions == {"Foto pública", "Foto privada"}


@pytest.mark.spec("RF-R1-14")
def test_articulo_incluye_las_etiquetas(client, make_user, make_trip, db_session) -> None:
    from app.models.tag import Tag, trip_tags

    _login(client, make_user)
    trip = make_trip(slug="mi-viaje", status=TripStatus.PUBLISHED)
    tag = Tag(name="montaña")
    db_session.add(tag)
    db_session.flush()
    db_session.execute(trip_tags.insert().values(trip_id=trip.id, tag_id=tag.id))
    db_session.flush()

    response = client.get(f"/api/trips/{trip.slug}")

    assert response.json()["tags"] == ["montaña"]


@pytest.mark.spec("RF-R1-14")
def test_articulo_de_borrador_devuelve_404(client, make_user, make_trip) -> None:
    _login(client, make_user)
    trip = make_trip(slug="borrador", status=TripStatus.DRAFT)

    response = client.get(f"/api/trips/{trip.slug}")

    assert response.status_code == 404


@pytest.mark.spec("RF-R1-14")
def test_articulo_inexistente_devuelve_404(client, make_user) -> None:
    _login(client, make_user)

    response = client.get("/api/trips/no-existe")

    assert response.status_code == 404


@pytest.mark.spec("RF-R1-14")
def test_articulo_de_borrador_y_articulo_inexistente_devuelven_el_mismo_404(
    client, make_user, make_trip
) -> None:
    _login(client, make_user)
    trip = make_trip(slug="borrador", status=TripStatus.DRAFT)

    draft_response = client.get(f"/api/trips/{trip.slug}")
    missing_response = client.get("/api/trips/no-existe-de-verdad")

    assert draft_response.status_code == missing_response.status_code == 404
    assert draft_response.json() == missing_response.json()
