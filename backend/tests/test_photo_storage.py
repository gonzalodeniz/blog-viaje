"""Implementa: RF-R1-14, RF-R1-15."""

from pathlib import Path

import pyvips
import pytest

from app.services.photo_storage import (
    WEB_VARIANT_MAX_DIMENSION,
    content_hash,
    generate_web_variant,
    save_original,
    sniff_image_format,
)


def _image_bytes(fmt: str, width: int, height: int) -> bytes:
    image = (pyvips.Image.black(width, height) + 128).cast("uchar")
    if fmt == "jpeg":
        return image.jpegsave_buffer(Q=80)
    if fmt == "png":
        return image.pngsave_buffer()
    return image.webpsave_buffer(Q=80)


@pytest.mark.spec("RF-R1-15")
def test_sniff_image_format_reconoce_jpeg_png_webp() -> None:
    assert sniff_image_format(_image_bytes("jpeg", 10, 10)) == "jpeg"
    assert sniff_image_format(_image_bytes("png", 10, 10)) == "png"
    assert sniff_image_format(_image_bytes("webp", 10, 10)) == "webp"


@pytest.mark.spec("RF-R1-15")
def test_sniff_image_format_rechaza_contenido_no_reconocido() -> None:
    assert sniff_image_format(b"no es una imagen") is None
    assert sniff_image_format(b"") is None


@pytest.mark.spec("RF-R1-15")
def test_content_hash_es_determinista() -> None:
    data = _image_bytes("jpeg", 10, 10)
    assert content_hash(data) == content_hash(data)
    assert content_hash(data) != content_hash(_image_bytes("jpeg", 11, 11))


@pytest.mark.spec("RF-R1-15")
def test_save_original_conserva_las_dimensiones(tmp_path: Path) -> None:
    data = _image_bytes("jpeg", 200, 100)

    original = save_original(
        tmp_path,
        data,
        image_format="jpeg",
        topic_slug="asia",
        trip_slug="japon",
        year=2024,
        content_hash_hex=content_hash(data),
    )

    assert original.width == 200
    assert original.height == 100
    assert (tmp_path / original.path).is_file()
    assert (tmp_path / original.path).read_bytes() == data


@pytest.mark.spec("RF-R1-15")
def test_generate_web_variant_no_agranda_imagenes_pequenas(tmp_path: Path) -> None:
    data = _image_bytes("jpeg", 200, 100)

    variant = generate_web_variant(
        tmp_path,
        data,
        photo_id="foto-1",
        topic_slug="asia",
        trip_slug="japon",
        year=2024,
        content_hash_hex=content_hash(data),
    )

    assert variant.width == 200
    assert variant.height == 100


@pytest.mark.spec("RF-R1-15")
def test_save_original_normaliza_slugs_con_intento_de_path_traversal(tmp_path: Path) -> None:
    data = _image_bytes("jpeg", 10, 10)

    original = save_original(
        tmp_path,
        data,
        image_format="jpeg",
        topic_slug="../../etc",
        trip_slug="../../../root",
        year=2024,
        content_hash_hex=content_hash(data),
    )

    absolute_path = (tmp_path / original.path).resolve()
    assert absolute_path.is_relative_to(tmp_path.resolve())
    assert ".." not in original.path


@pytest.mark.spec("RF-R1-15")
def test_generate_web_variant_reduce_imagenes_grandes_al_maximo(tmp_path: Path) -> None:
    data = _image_bytes("jpeg", WEB_VARIANT_MAX_DIMENSION + 400, 900)

    variant = generate_web_variant(
        tmp_path,
        data,
        photo_id="foto-1",
        topic_slug="asia",
        trip_slug="japon",
        year=2024,
        content_hash_hex=content_hash(data),
    )

    assert variant.width == WEB_VARIANT_MAX_DIMENSION
    assert variant.height < 900
    assert (tmp_path / variant.path).suffix == ".webp"
