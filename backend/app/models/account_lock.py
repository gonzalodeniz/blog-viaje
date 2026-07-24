"""Implementa: RF-R1-11.

Esquema mínimo para que `bitacora-cli unlock`/`list-users` (TASK-R1-011)
tengan algo que leer y limpiar. El *escritor* real de esta tabla — el
enforcement del bloqueo tras 5 fallos consecutivos (RF-R1-03/04) — todavía
no existe; llega en una tarea futura de WP-R1-2. Hasta entonces no habrá
filas en producción y esta tabla se queda vacía, pero la CLI ya queda lista
para cuando las haya.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AccountLock(Base):
    __tablename__ = "account_locks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Por username declarado, no FK a users: igual que login_attempts
    # (SPEC-MASTER §8), el bloqueo se evalúa sobre el usuario que se
    # afirmó en el intento de login, exista o no de verdad (RF-R1-04).
    username: Mapped[str] = mapped_column(String(80), nullable=False)
    locked_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Backoff exponencial 15 -> 30 -> 60 min (RF-R1-03): cuenta bloqueos
    # consecutivos para calcular la duración del siguiente.
    consecutive_locks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
