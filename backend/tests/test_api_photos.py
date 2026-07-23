"""Implementa: RF-R1-14."""

import pyvips
import pytest


def _login_admin(client, make_user) -> str:
    username, password = "gonzalo", "una-contraseña-larga-123"
    make_user(username=username, password=password, role="admin")
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def _jpeg_bytes(width: int = 40, height: int = 30) -> bytes:
    image = (pyvips.Image.black(width, height) + 128).cast("uchar")
    return image.jpegsave_buffer(Q=80)


def _upload_photo(client, csrf: str, trip_id) -> str:
    response = client.post(
        f"/api/admin/trips/{trip_id}/photos",
        files={"files": ("foto.jpg", _jpeg_bytes(), "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )
    return response.json()["created"][0]["id"]


@pytest.mark.spec("RF-R1-14")
def test_servir_foto_sin_sesion_devuelve_401(client, make_trip) -> None:
    make_trip()
    response = client.get("/api/photos/00000000-0000-0000-0000-000000000000/file")
    assert response.status_code == 401


@pytest.mark.spec("RF-R1-14")
def test_servir_foto_con_sesion_devuelve_la_variante_web(client, make_user, make_trip) -> None:
    csrf = _login_admin(client, make_user)
    trip = make_trip()
    photo_id = _upload_photo(client, csrf, trip.id)

    response = client.get(f"/api/photos/{photo_id}/file")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert len(response.content) > 0


@pytest.mark.spec("RF-R1-14")
def test_servir_foto_sin_variante_generada_devuelve_404(client, make_user, make_photo) -> None:
    _login_admin(client, make_user)
    photo = make_photo()

    response = client.get(f"/api/photos/{photo.id}/file")

    assert response.status_code == 404


@pytest.mark.spec("RF-R1-14")
def test_servir_foto_inexistente_devuelve_404(client, make_user) -> None:
    _login_admin(client, make_user)

    response = client.get("/api/photos/00000000-0000-0000-0000-000000000000/file")

    assert response.status_code == 404
