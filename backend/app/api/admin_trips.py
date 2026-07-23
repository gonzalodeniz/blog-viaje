"""Implementa: RF-R1-15, RF-R1-18."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import require_admin, require_csrf
from app.core.slugify import slugify
from app.db.session import get_db
from app.models.photo import Photo
from app.models.tag import Tag
from app.models.topic import Topic
from app.models.trip import Trip, TripStatus
from app.services.html_sanitizer import render_content_html

router = APIRouter(
    prefix="/api/admin/trips",
    tags=["admin-trips"],
    dependencies=[Depends(require_admin)],
)


class TripCreate(BaseModel):
    title: str
    topic_id: uuid.UUID
    place: str | None = None
    trip_start: date | None = None
    trip_end: date | None = None
    excerpt: str | None = None
    cover_photo_id: uuid.UUID | None = None
    tag_names: list[str] = []
    content_json: dict | None = None


class TripUpdate(BaseModel):
    title: str | None = None
    topic_id: uuid.UUID | None = None
    place: str | None = None
    trip_start: date | None = None
    trip_end: date | None = None
    excerpt: str | None = None
    cover_photo_id: uuid.UUID | None = None
    tag_names: list[str] | None = None
    content_json: dict | None = None
    status: TripStatus | None = None


class TripAdminOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    topic_id: uuid.UUID
    place: str | None
    trip_start: date | None
    trip_end: date | None
    excerpt: str | None
    cover_photo_id: uuid.UUID | None
    status: TripStatus
    tags: list[str]
    content_json: dict | None
    content_html: str | None


def _to_out(trip: Trip) -> TripAdminOut:
    return TripAdminOut(
        id=trip.id,
        slug=trip.slug,
        title=trip.title,
        topic_id=trip.topic_id,
        place=trip.place,
        trip_start=trip.trip_start,
        trip_end=trip.trip_end,
        excerpt=trip.excerpt,
        cover_photo_id=trip.cover_photo_id,
        status=trip.status,
        tags=sorted(tag.name for tag in trip.tags),
        content_json=trip.content_json,
        content_html=trip.content_html,
    )


def _get_or_404(db: DbSession, trip_id: uuid.UUID) -> Trip:
    trip = db.get(Trip, trip_id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")
    return trip


def _require_topic(db: DbSession, topic_id: uuid.UUID) -> None:
    if db.get(Topic, topic_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El tema indicado no existe")


def _require_photo(db: DbSession, photo_id: uuid.UUID) -> None:
    if db.get(Photo, photo_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La foto de portada indicada no existe")


def _resolve_tags(db: DbSession, tag_names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in dict.fromkeys(n.strip() for n in tag_names if n.strip()):
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if tag is None:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


def _unique_slug(db: DbSession, title: str) -> str:
    base = slugify(title)
    slug = base
    suffix = 2
    while db.scalar(select(Trip).where(Trip.slug == slug)) is not None:
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


@router.get("", response_model=list[TripAdminOut])
def list_trips(db: DbSession = Depends(get_db)) -> list[TripAdminOut]:
    trips = db.scalars(select(Trip).order_by(Trip.created_at.desc())).all()
    return [_to_out(t) for t in trips]


@router.get("/{trip_id}", response_model=TripAdminOut)
def get_trip(trip_id: uuid.UUID, db: DbSession = Depends(get_db)) -> TripAdminOut:
    return _to_out(_get_or_404(db, trip_id))


@router.post("", response_model=TripAdminOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_trip(body: TripCreate, db: DbSession = Depends(get_db)) -> TripAdminOut:
    _require_topic(db, body.topic_id)
    if body.cover_photo_id is not None:
        _require_photo(db, body.cover_photo_id)

    trip = Trip(
        title=body.title,
        slug=_unique_slug(db, body.title),
        topic_id=body.topic_id,
        place=body.place,
        trip_start=body.trip_start,
        trip_end=body.trip_end,
        excerpt=body.excerpt,
        cover_photo_id=body.cover_photo_id,
        content_json=body.content_json,
        content_html=render_content_html(body.content_json) if body.content_json else None,
        status=TripStatus.DRAFT,
    )
    trip.tags = _resolve_tags(db, body.tag_names)
    db.add(trip)
    db.flush()
    return _to_out(trip)


@router.put("/{trip_id}", response_model=TripAdminOut, dependencies=[Depends(require_csrf)])
def update_trip(trip_id: uuid.UUID, body: TripUpdate, db: DbSession = Depends(get_db)) -> TripAdminOut:
    trip = _get_or_404(db, trip_id)
    changes = body.model_dump(exclude_unset=True)

    if "topic_id" in changes:
        _require_topic(db, changes["topic_id"])
    if "cover_photo_id" in changes and changes["cover_photo_id"] is not None:
        _require_photo(db, changes["cover_photo_id"])
    if "tag_names" in changes:
        trip.tags = _resolve_tags(db, changes.pop("tag_names"))
    if "content_json" in changes:
        trip.content_html = render_content_html(changes["content_json"])

    for field, value in changes.items():
        setattr(trip, field, value)

    db.flush()
    return _to_out(trip)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def delete_trip(trip_id: uuid.UUID, db: DbSession = Depends(get_db)) -> None:
    # Sin try/except de IntegrityError aquí: a diferencia de topics, nada
    # referencia a trips con ON DELETE RESTRICT (fotos y trip_tags son
    # CASCADE), así que borrar un viaje nunca puede violar una FK.
    trip = _get_or_404(db, trip_id)
    db.delete(trip)
    db.flush()
