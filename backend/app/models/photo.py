"""Implementa: RF-R1-14, RF-R1-15."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PhotoVisibility(str, enum.Enum):
    PRIVATE = "private"
    PUBLIC = "public"


class PhotoVariantKind(str, enum.Enum):
    THUMB = "thumb"
    MEDIUM = "medium"
    LARGE = "large"


class PhotoVariantFormat(str, enum.Enum):
    WEBP = "webp"
    JPEG = "jpeg"
    AVIF = "avif"


class Photo(Base):
    __tablename__ = "photos"
    __table_args__ = (UniqueConstraint("trip_id", "content_hash", name="uq_photos_trip_content_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
    )
    # Ruta bajo media/originals/ (SPEC-MASTER §7.5); el original nunca se
    # modifica ni se sirve directamente (CLAUDE.md, regla de producto).
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    taken_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    gps_lat: Mapped[float | None] = mapped_column(Numeric(9, 6))
    gps_lon: Mapped[float | None] = mapped_column(Numeric(9, 6))
    visibility: Mapped[PhotoVisibility] = mapped_column(
        Enum(
            PhotoVisibility,
            name="photo_visibility",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=PhotoVisibility.PRIVATE,
    )
    caption: Mapped[str | None] = mapped_column(String(500))
    alt_text: Mapped[str | None] = mapped_column(String(300))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PhotoVariant(Base):
    __tablename__ = "photo_variants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    photo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[PhotoVariantKind] = mapped_column(
        Enum(
            PhotoVariantKind,
            name="photo_variant_kind",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    format: Mapped[PhotoVariantFormat] = mapped_column(
        Enum(
            PhotoVariantFormat,
            name="photo_variant_format",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    # Ruta bajo media/derived/ (SPEC-MASTER §7.5); regenerable desde el
    # original con `bitacora-cli regenerate-derived`.
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    bytes: Mapped[int] = mapped_column(Integer, nullable=False)
