"""Implementa: RF-R1-13, RF-R1-14, RF-R1-15, RF-R1-18."""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.tag import Tag, trip_tags


class TripStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(500))
    # RF-R1-18: JSON de ProseMirror (fuente editable) + HTML sanitizado en
    # servidor con lista blanca (lo genera la capa de aplicación, no esta
    # migración) para servirlo directamente en la vista de lectura.
    content_json: Mapped[dict | None] = mapped_column(JSONB)
    content_html: Mapped[str | None] = mapped_column(Text)
    cover_photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("photos.id", ondelete="SET NULL", use_alter=True, name="fk_trips_cover_photo_id"),
    )
    place: Mapped[str | None] = mapped_column(String(200))
    trip_start: Mapped[date | None] = mapped_column(Date)
    trip_end: Mapped[date | None] = mapped_column(Date)
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_status", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=TripStatus.DRAFT,
    )
    # Poblado por un trigger/actualización de aplicación a partir de title +
    # content_html; el índice GIN se crea en la migración. El endpoint de
    # búsqueda (query=) no forma parte de esta tarea.
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tags: Mapped[list[Tag]] = relationship(secondary=trip_tags)
