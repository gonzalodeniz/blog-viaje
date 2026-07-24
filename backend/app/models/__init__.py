"""Registra todos los modelos en app.db.base.Base.metadata para Alembic."""

from app.models.account_lock import AccountLock
from app.models.audit_log import AuditLog
from app.models.photo import Photo, PhotoVariant
from app.models.session import Session
from app.models.tag import Tag, trip_tags
from app.models.topic import Topic
from app.models.trip import Trip
from app.models.user import User

__all__ = [
    "AccountLock",
    "AuditLog",
    "Photo",
    "PhotoVariant",
    "Session",
    "Tag",
    "trip_tags",
    "Topic",
    "Trip",
    "User",
]
