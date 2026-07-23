"""Implementa: RF-R1-02."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # SHA-256 del token de sesión (256 bits, generado en app.core.security);
    # el token en claro solo existe en la cookie del navegador, nunca en BD.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    # Expiración deslizante por inactividad, recalculada en cada petición
    # autenticada (RF-R1-02); nunca puede superar absolute_expires_at.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    absolute_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # No está en el boceto de esquema de SPEC-MASTER §7.3, pero hace falta
    # para saber qué TTL (24h u opción "remember me" de 30 días, ambos
    # configurables) usar al renovar la expiración deslizante en cada
    # petición — ver TASK-R1-007, nota de implementación.
    remember: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip: Mapped[str | None] = mapped_column(String(45))
