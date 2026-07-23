"""Fixtures compartidas: sesión de PostgreSQL real con el esquema migrado."""

from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def _esquema_migrado() -> None:
    """Aplica las migraciones de Alembic una vez contra la base de datos de test."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", get_settings().database_url)
    command.upgrade(cfg, "head")


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Sesión real de PostgreSQL, aislada por transacción y revertida al terminar el test.

    Usa el patrón estándar de SQLAlchemy de SAVEPOINT anidado: un test que
    fuerza un IntegrityError (para verificar una constraint) cierra su propia
    subtransacción, así que hace falta reabrir el SAVEPOINT en cada
    `after_transaction_end` para que el resto del test siga pudiendo usar la
    sesión.
    """
    engine = create_engine(get_settings().database_url)
    connection = engine.connect()
    outer_transaction = connection.begin()
    connection.begin_nested()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    @event.listens_for(session, "after_transaction_end")
    def _reabrir_savepoint(session: Session, transaction: object) -> None:
        if connection.closed:
            return
        if not connection.in_nested_transaction():
            connection.begin_nested()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def make_topic(db_session: Session):
    from app.models.topic import Topic

    def _make(**kwargs: object) -> Topic:
        defaults = {"name": "Europa", "slug": "europa"}
        defaults.update(kwargs)
        topic = Topic(**defaults)
        db_session.add(topic)
        db_session.flush()
        return topic

    return _make


@pytest.fixture
def make_trip(db_session: Session, make_topic):
    from app.models.trip import Trip

    def _make(**kwargs: object) -> Trip:
        topic = kwargs.pop("topic", None) or make_topic()
        defaults = {"topic_id": topic.id, "title": "Viaje", "slug": "viaje"}
        defaults.update(kwargs)
        trip = Trip(**defaults)
        db_session.add(trip)
        db_session.flush()
        return trip

    return _make


@pytest.fixture
def make_user(db_session: Session):
    from app.core.security import hash_password
    from app.models.user import User

    def _make(**kwargs: object) -> User:
        password = kwargs.pop("password", "una-contraseña-larga-123")
        defaults = {"username": "gonzalo", "password_hash": hash_password(password)}
        defaults.update(kwargs)
        user = User(**defaults)
        db_session.add(user)
        db_session.flush()
        return user

    return _make


@pytest.fixture
def client(db_session: Session, tmp_path):
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.db.session import get_db
    from app.main import app

    def _override_get_db():
        yield db_session

    # media_root aislado por test: las subidas de fotos (TASK-R1-010) no
    # deben escribir en el media/ real del checkout.
    test_settings = get_settings().model_copy(update={"media_root": str(tmp_path / "media")})

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings
    try:
        # base_url en https: las cookies de sesión/CSRF se emiten con
        # Secure=True (RF-R1-02) y el cliente de test descartaría esas
        # cookies de su jar entre peticiones si el esquema fuera http.
        with TestClient(app, base_url="https://testserver") as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_photo(db_session: Session, make_trip, make_topic):
    from app.models.photo import Photo

    def _make(**kwargs: object) -> Photo:
        trip = kwargs.pop("trip", None) or make_trip()
        topic_id = kwargs.pop("topic_id", None) or trip.topic_id
        defaults = {
            "trip_id": trip.id,
            "topic_id": topic_id,
            "original_path": "originals/foo.jpg",
            "content_hash": "hash-1",
            "width": 100,
            "height": 100,
        }
        defaults.update(kwargs)
        photo = Photo(**defaults)
        db_session.add(photo)
        db_session.flush()
        return photo

    return _make
