"""Implementa: RF-R1-01, RF-R1-02."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # "admin" | "lector" (RF-R1-07). Columna presente por el esquema fijado en
    # SPEC-MASTER §7.3; la autorización por rol todavía no se aplica en
    # ningún endpoint (llega en una tarea posterior de WP-R1-2).
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="admin")
    # RF-R1-20: fuerza la pantalla de cambio de contraseña antes de cualquier
    # otra acción. Columna presente pero sin lógica que la aplique todavía.
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
