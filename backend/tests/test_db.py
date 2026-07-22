import pytest
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import get_db


@pytest.mark.spec("RNF-R1-07")
def test_base_es_una_base_declarativa() -> None:
    assert hasattr(Base, "metadata")


@pytest.mark.spec("RNF-R1-07")
def test_get_db_produce_y_cierra_una_sesion() -> None:
    gen = get_db()
    db = next(gen)

    assert isinstance(db, Session)

    with pytest.raises(StopIteration):
        next(gen)
