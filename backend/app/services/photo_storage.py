"""Implementa: RF-R1-14, RF-R1-15.

Almacenamiento de fotos: validación por firma binaria, hash de contenido y
generación de la única variante web que necesita R1 (SPEC-R1: "subida
simple, original + una versión web razonable"). El pipeline completo de
variantes (thumb/large/AVIF/SSIM adaptativo) es RF-R2-12/13, no esto.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyvips

from app.core.slugify import slugify

WEB_VARIANT_MAX_DIMENSION = 1600
WEB_VARIANT_QUALITY = 82

_EXTENSIONS = {"jpeg": "jpg", "png": "png", "webp": "webp"}


def sniff_image_format(data: bytes) -> str | None:
    """Identifica el formato por firma binaria — nunca por extensión/Content-Type."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _trip_folder(topic_slug: str, trip_slug: str, year: int) -> str:
    # Se re-normalizan aquí, aunque ya deberían ser slugs válidos en BD: son
    # la única parte de la ruta que viene (indirectamente) de texto que
    # introdujo un cliente (RF-R1-16), y una ruta de fichero no es un sitio
    # donde asumir que un valor ya validado en otra capa sigue siendo seguro.
    return f"{slugify(topic_slug)}/{year}-{slugify(trip_slug)}"


@dataclass
class StoredOriginal:
    path: str
    width: int
    height: int


def save_original(
    media_root: Path,
    data: bytes,
    *,
    image_format: str,
    topic_slug: str,
    trip_slug: str,
    year: int,
    content_hash_hex: str,
) -> StoredOriginal:
    folder = media_root / "originals" / _trip_folder(topic_slug, trip_slug, year)
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{content_hash_hex[:8]}.{_EXTENSIONS[image_format]}"
    absolute_path = folder / filename
    absolute_path.write_bytes(data)

    image = pyvips.Image.new_from_buffer(data, "")
    return StoredOriginal(
        path=str(absolute_path.relative_to(media_root)), width=image.width, height=image.height
    )


@dataclass
class GeneratedVariant:
    path: str
    width: int
    height: int
    bytes_size: int


def generate_web_variant(
    media_root: Path,
    data: bytes,
    *,
    photo_id: str,
    topic_slug: str,
    trip_slug: str,
    year: int,
    content_hash_hex: str,
) -> GeneratedVariant:
    image = pyvips.Image.new_from_buffer(data, "")
    scale = min(1.0, WEB_VARIANT_MAX_DIMENSION / max(image.width, image.height))
    if scale < 1.0:
        image = image.resize(scale)

    folder = media_root / "derived" / _trip_folder(topic_slug, trip_slug, year)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{photo_id}_{content_hash_hex[:8]}_medium.webp"
    absolute_path = folder / filename
    image.webpsave(str(absolute_path), Q=WEB_VARIANT_QUALITY)

    return GeneratedVariant(
        path=str(absolute_path.relative_to(media_root)),
        width=image.width,
        height=image.height,
        bytes_size=absolute_path.stat().st_size,
    )
