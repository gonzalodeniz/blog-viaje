"""Implementa: RF-R1-13, RF-R1-14, RF-R1-15, RF-R1-16, RF-R1-18.

Verifica contra PostgreSQL real las constraints clave del esquema de
contenido: UNIQUE de slugs/hashes y el comportamiento CASCADE/RESTRICT/SET
NULL de las claves foráneas.
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.photo import Photo, PhotoVariant
from app.models.tag import Tag, trip_tags
from app.models.topic import Topic
from app.models.trip import Trip


@pytest.mark.spec("RF-R1-16")
def test_topic_slug_es_unico(db_session, make_topic) -> None:
    make_topic(name="Asia", slug="asia")

    with pytest.raises(IntegrityError):
        db_session.add(Topic(name="Asia 2", slug="asia"))
        db_session.flush()


@pytest.mark.spec("RF-R1-13")
def test_trip_slug_es_unico(db_session, make_topic, make_trip) -> None:
    topic = make_topic()
    make_trip(topic=topic, slug="mi-viaje")

    with pytest.raises(IntegrityError):
        db_session.add(Trip(topic_id=topic.id, title="Otro", slug="mi-viaje"))
        db_session.flush()


@pytest.mark.spec("RF-R1-15")
def test_photo_content_hash_es_unico_por_viaje(db_session, make_trip, make_photo) -> None:
    trip = make_trip()
    make_photo(trip=trip, content_hash="abc123")

    with pytest.raises(IntegrityError):
        db_session.add(
            Photo(
                trip_id=trip.id,
                topic_id=trip.topic_id,
                original_path="originals/otra.jpg",
                content_hash="abc123",
                width=10,
                height=10,
            )
        )
        db_session.flush()


@pytest.mark.spec("RF-R1-15")
def test_photo_content_hash_repetido_en_otro_viaje_es_valido(db_session, make_topic, make_trip, make_photo) -> None:
    topic = make_topic()
    make_photo(trip=make_trip(topic=topic, slug="viaje-1"), content_hash="mismo-hash")
    make_photo(trip=make_trip(topic=topic, slug="viaje-2"), content_hash="mismo-hash")

    db_session.flush()


@pytest.mark.spec("RF-R1-16")
def test_borrar_topic_con_viajes_falla_por_restrict(db_session, make_topic, make_trip) -> None:
    topic = make_topic()
    make_trip(topic=topic)

    db_session.delete(topic)
    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.spec("RF-R1-13")
def test_borrar_trip_hace_cascade_sobre_sus_fotos(db_session, make_trip, make_photo) -> None:
    trip = make_trip()
    photo = make_photo(trip=trip)
    photo_id = photo.id

    db_session.delete(trip)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(Photo, photo_id) is None


@pytest.mark.spec("RF-R1-15")
def test_borrar_photo_hace_cascade_sobre_sus_variantes(db_session, make_photo) -> None:
    photo = make_photo()
    variant = PhotoVariant(
        photo_id=photo.id,
        kind="thumb",
        format="webp",
        path="derived/thumb.webp",
        width=10,
        height=10,
        bytes=100,
    )
    db_session.add(variant)
    db_session.flush()
    variant_id = variant.id

    db_session.delete(photo)
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(PhotoVariant, variant_id) is None


@pytest.mark.spec("RF-R1-14")
def test_borrar_photo_referenciada_como_portada_pone_null(db_session, make_trip, make_photo) -> None:
    trip = make_trip()
    photo = make_photo(trip=trip)
    trip.cover_photo_id = photo.id
    db_session.flush()

    db_session.delete(photo)
    db_session.flush()
    db_session.refresh(trip)

    assert trip.cover_photo_id is None


@pytest.mark.spec("RF-R1-15")
def test_borrar_trip_hace_cascade_sobre_trip_tags(db_session, make_trip) -> None:
    trip = make_trip()
    tag = Tag(name=f"tag-{uuid.uuid4()}")
    db_session.add(tag)
    db_session.flush()
    db_session.execute(trip_tags.insert().values(trip_id=trip.id, tag_id=tag.id))
    db_session.flush()

    db_session.delete(trip)
    db_session.flush()

    rows = db_session.execute(
        trip_tags.select().where(trip_tags.c.tag_id == tag.id)
    ).fetchall()
    assert rows == []
