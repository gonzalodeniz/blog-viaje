"""Base declarativa de SQLAlchemy: todos los modelos heredan de aquí."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
