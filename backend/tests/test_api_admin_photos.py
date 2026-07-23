"""Implementa: RF-R1-14, RF-R1-15."""

import pyvips
import pytest

from app.models.photo import Photo


def _login(client, make_user, *, role: str = "admin") -> str:
    username, password = "gonzalo", "una-contraseña-larga-123"
    make_user(username=username, password=password, role=role)
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.cookies["csrf_token"]


def _jpeg_bytes(width: int = 40, height: int = 30) -> bytes:
    image = pyvips.Image.black(width, height) + 128
    return image.cast("uchar").jpegsave_buffer(Q=80)


@pytest.mark.spec("RF-R1-14")
def test_subir_foto_sin_sesion_devuelve_401(client, make_trip) -> None:
    trip = make_trip()
    response = client.post(
        f"/api/admin/trips/{trip.id}/photos", files={"files": ("foto.jpg", _jpeg_bytes(), "image/jpeg")}
    )
    assert response.status_code == 401


@pytest.mark.spec("RF-R1-15")
def test_subir_foto_sin_rol_admin_devuelve_403(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user, role="lector")
    trip = make_trip()

    response = client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files={"files": ("foto.jpg", _jpeg_bytes(), "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 403


@pytest.mark.spec("RF-R1-15")
def test_subir_foto_valida_crea_photo_y_variante(client, make_user, make_trip, db_session) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files={"files": ("foto.jpg", _jpeg_bytes(width=200, height=100), "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["created"]) == 1
    assert body["errors"] == []
    assert body["created"][0]["width"] == 200
    assert body["created"][0]["height"] == 100

    photo = db_session.get(Photo, body["created"][0]["id"])
    assert photo is not None
    assert photo.original_path.endswith(".jpg")


@pytest.mark.spec("RF-R1-15")
def test_subir_varias_fotos_a_la_vez(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files=[
            ("files", ("uno.jpg", _jpeg_bytes(), "image/jpeg")),
            ("files", ("dos.jpg", _jpeg_bytes(width=60, height=60), "image/jpeg")),
        ],
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 201
    assert len(response.json()["created"]) == 2


@pytest.mark.spec("RF-R1-15")
def test_subir_archivo_con_firma_invalida_se_rechaza(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()

    response = client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files={"files": ("foto.jpg", b"esto no es una imagen de verdad", "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created"] == []
    assert body["errors"][0]["detail"] == "Formato de imagen no admitido"


@pytest.mark.spec("RF-R1-15")
def test_subir_archivo_demasiado_grande_se_rechaza(client, make_user, make_trip, monkeypatch) -> None:
    from app.core.config import get_settings
    from app.main import app

    csrf = _login(client, make_user)
    trip = make_trip()
    data = _jpeg_bytes(width=500, height=500)

    # Reduce el límite en la misma instancia de Settings que ya usa el
    # cliente de test (con su media_root aislado en tmp_path), en vez de
    # sustituirla por otra que perdería ese aislamiento.
    active_settings = app.dependency_overrides[get_settings]()
    monkeypatch.setattr(active_settings, "photo_max_upload_bytes", len(data) - 1)

    response = client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files={"files": ("foto.jpg", data, "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )

    body = response.json()
    assert body["created"] == []
    assert body["errors"][0]["detail"] == "Archivo demasiado grande"


@pytest.mark.spec("RF-R1-15")
def test_subir_la_misma_foto_dos_veces_al_mismo_viaje_devuelve_error(client, make_user, make_trip) -> None:
    csrf = _login(client, make_user)
    trip = make_trip()
    data = _jpeg_bytes()

    client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files={"files": ("foto.jpg", data, "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )
    response = client.post(
        f"/api/admin/trips/{trip.id}/photos",
        files={"files": ("foto.jpg", data, "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )

    body = response.json()
    assert body["created"] == []
    assert "ya se subió" in body["errors"][0]["detail"]


@pytest.mark.spec("RF-R1-15")
def test_subir_foto_a_viaje_inexistente_devuelve_404(client, make_user) -> None:
    csrf = _login(client, make_user)

    response = client.post(
        "/api/admin/trips/00000000-0000-0000-0000-000000000000/photos",
        files={"files": ("foto.jpg", _jpeg_bytes(), "image/jpeg")},
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 404
