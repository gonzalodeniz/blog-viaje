"""Implementa: RF-R1-13, RF-R1-14."""

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.photo import Photo
from app.models.topic import Topic
from app.models.trip import Trip, TripStatus
from app.models.user import User

router = APIRouter(prefix="/api/trips", tags=["trips"])


class TopicSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class TripListItem(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    excerpt: str | None
    topic: TopicSummary
    trip_start: date | None
    trip_end: date | None
    cover_photo_id: uuid.UUID | None


class PhotoSummary(BaseModel):
    id: uuid.UUID
    caption: str | None
    alt_text: str | None
    width: int
    height: int
    taken_at: datetime | None


class TripDetail(TripListItem):
    content_html: str
    place: str | None
    tags: list[str]
    photos: list[PhotoSummary]


def _topic_summary(topic: Topic) -> TopicSummary:
    return TopicSummary(id=topic.id, name=topic.name, slug=topic.slug)


def _trip_list_item(trip: Trip, topic: Topic) -> TripListItem:
    return TripListItem(
        id=trip.id,
        slug=trip.slug,
        title=trip.title,
        excerpt=trip.excerpt,
        topic=_topic_summary(topic),
        trip_start=trip.trip_start,
        trip_end=trip.trip_end,
        cover_photo_id=trip.cover_photo_id,
    )


@router.get("", response_model=list[TripListItem])
def list_trips(
    db: DbSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[TripListItem]:
    rows = db.execute(
        select(Trip, Topic)
        .join(Topic, Trip.topic_id == Topic.id)
        .where(Trip.status == TripStatus.PUBLISHED)
        .order_by(Trip.trip_start.desc().nulls_last(), Trip.created_at.desc())
    ).all()
    return [_trip_list_item(trip, topic) for trip, topic in rows]


@router.get("/{slug}", response_model=TripDetail)
def get_trip(
    slug: str,
    db: DbSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> TripDetail:
    row = db.execute(
        select(Trip, Topic)
        .join(Topic, Trip.topic_id == Topic.id)
        .where(Trip.slug == slug, Trip.status == TripStatus.PUBLISHED)
    ).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Viaje no encontrado")
    trip, topic = row

    photos = db.scalars(
        select(Photo)
        .where(Photo.trip_id == trip.id, Photo.deleted_at.is_(None))
        .order_by(Photo.taken_at)
    ).all()

    base = _trip_list_item(trip, topic)
    return TripDetail(
        **base.model_dump(),
        content_html=trip.content_html or "",
        place=trip.place,
        tags=sorted(tag.name for tag in trip.tags),
        photos=[
            PhotoSummary(
                id=photo.id,
                caption=photo.caption,
                alt_text=photo.alt_text,
                width=photo.width,
                height=photo.height,
                taken_at=photo.taken_at,
            )
            for photo in photos
        ],
    )
