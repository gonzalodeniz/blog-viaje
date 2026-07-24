"""Implementa: RF-R1-05."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoginAttemptResult(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    LOCKED = "locked"


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Username tal y como se declaró en el intento, exista o no de verdad
    # (RF-R1-04): sin FK a users, igual que account_locks.
    username_claimed: Mapped[str] = mapped_column(String(80), nullable=False)
    result: Mapped[LoginAttemptResult] = mapped_column(
        Enum(LoginAttemptResult, name="login_attempt_result", native_enum=True, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
