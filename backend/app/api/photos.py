"""Implementa: RF-R1-14.

Sirve únicamente la variante web (`derived/`) de una foto a cualquier
sesión autenticada; los originales (`originals/`) no se sirven jamás por
ningún endpoint (regla de producto no negociable).
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.photo import PhotoVariant
from app.models.user import User

router = APIRouter(prefix="/api/photos", tags=["photos"])


@router.get("/{photo_id}/file")
def get_photo_file(
    photo_id: uuid.UUID,
    db: DbSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _current_user: User = Depends(get_current_user),
) -> FileResponse:
    variant = db.scalar(
        select(PhotoVariant).where(PhotoVariant.photo_id == photo_id, PhotoVariant.kind == "medium")
    )
    if variant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto no encontrada")

    media_root = Path(settings.media_root).resolve()
    absolute_path = (media_root / variant.path).resolve()
    if not absolute_path.is_relative_to(media_root) or not absolute_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Foto no encontrada")

    return FileResponse(absolute_path, media_type="image/webp")
