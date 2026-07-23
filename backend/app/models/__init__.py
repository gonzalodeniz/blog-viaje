"""Registra todos los modelos en app.db.base.Base.metadata para Alembic."""

from app.models.audit_log import AuditLog
from app.models.photo import Photo, PhotoVariant
from app.models.tag import Tag, trip_tags
from app.models.topic import Topic
from app.models.trip import Trip

__all__ = [
    "AuditLog",
    "Photo",
    "PhotoVariant",
    "Tag",
    "trip_tags",
    "Topic",
    "Trip",
]
