"""Implementa: RF-R1-14, RF-R1-15."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.api.deps import require_admin, require_csrf
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.photo import Photo, PhotoVariant
from app.models.topic import Topic
from app.models.trip import Trip
from app.services.photo_storage import content_hash, generate_web_variant, save_original, sniff_image_format

router = APIRouter(
    prefix="/api/admin/trips/{trip_id}/photos",
    tags=["admin-photos"],
    dependencies=[Depends(require_admin), Depends(require_csrf)],
)


class UploadedPhotoOut(BaseModel):
    id: uuid.UUID
    filename: str
    width: int
    height: int


class PhotoUploadError(BaseModel):
    filename: str
    detail: str


class UploadPhotosResponse(BaseModel):
    created: list[UploadedPhotoOut]
    errors: list[PhotoUploadError]


@router.post("", response_model=UploadPhotosResponse, status_code=status.HTTP_201_CREATED)
async def upload_photos(
    trip_id: uuid.UUID,
    files: list[UploadFile],
    db: DbSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UploadPhotosResponse:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")
    topic = db.get(Topic, trip.topic_id)

    media_root = Path(settings.media_root)
    year = trip.trip_start.year if trip.trip_start else datetime.now(timezone.utc).year

    created: list[UploadedPhotoOut] = []
    errors: list[PhotoUploadError] = []

    for upload in files:
        filename = upload.filename or ""
        data = await upload.read()

        if len(data) > settings.photo_max_upload_bytes:
            errors.append(PhotoUploadError(filename=filename, detail="Archivo demasiado grande"))
            continue

        image_format = sniff_image_format(data)
        if image_format is None:
            errors.append(PhotoUploadError(filename=filename, detail="Formato de imagen no admitido"))
            continue

        digest = content_hash(data)
        already_exists = db.scalar(
            select(Photo).where(Photo.trip_id == trip.id, Photo.content_hash == digest)
        )
        if already_exists is not None:
            errors.append(PhotoUploadError(filename=filename, detail="Esta foto ya se subió a este viaje"))
            continue

        original = save_original(
            media_root,
            data,
            image_format=image_format,
            topic_slug=topic.slug,
            trip_slug=trip.slug,
            year=year,
            content_hash_hex=digest,
        )

        photo = Photo(
            trip_id=trip.id,
            topic_id=trip.topic_id,
            original_path=original.path,
            content_hash=digest,
            width=original.width,
            height=original.height,
        )
        db.add(photo)
        try:
            db.flush()
        except IntegrityError:
            # Backstop de condición de carrera: dos subidas concurrentes del
            # mismo contenido al mismo viaje pueden pasar ambas la
            # comprobación de arriba antes de que ninguna haga flush().
            db.rollback()
            errors.append(PhotoUploadError(filename=filename, detail="Esta foto ya se subió a este viaje"))
            continue

        variant = generate_web_variant(
            media_root,
            data,
            photo_id=str(photo.id),
            topic_slug=topic.slug,
            trip_slug=trip.slug,
            year=year,
            content_hash_hex=digest,
        )
        db.add(
            PhotoVariant(
                photo_id=photo.id,
                kind="medium",
                format="webp",
                path=variant.path,
                width=variant.width,
                height=variant.height,
                bytes=variant.bytes_size,
            )
        )
        db.flush()

        created.append(UploadedPhotoOut(id=photo.id, filename=filename, width=photo.width, height=photo.height))

    return UploadPhotosResponse(created=created, errors=errors)
