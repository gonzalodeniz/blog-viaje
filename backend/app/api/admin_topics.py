"""Implementa: RF-R1-16."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from app.api.deps import require_admin, require_csrf
from app.db.session import get_db
from app.models.topic import Topic
from app.models.user import User

router = APIRouter(
    prefix="/api/admin/topics",
    tags=["admin-topics"],
    dependencies=[Depends(require_admin)],
)


class TopicCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    color: str | None = None


class TopicUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    color: str | None = None


class TopicOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    color: str | None


def _to_out(topic: Topic) -> TopicOut:
    return TopicOut(
        id=topic.id, name=topic.name, slug=topic.slug, description=topic.description, color=topic.color
    )


def _get_or_404(db: DbSession, topic_id: uuid.UUID) -> Topic:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tema no encontrado")
    return topic


@router.get("", response_model=list[TopicOut])
def list_topics(db: DbSession = Depends(get_db)) -> list[TopicOut]:
    topics = db.scalars(select(Topic).order_by(Topic.name)).all()
    return [_to_out(t) for t in topics]


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: uuid.UUID, db: DbSession = Depends(get_db)) -> TopicOut:
    return _to_out(_get_or_404(db, topic_id))


@router.post("", response_model=TopicOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_csrf)])
def create_topic(body: TopicCreate, db: DbSession = Depends(get_db)) -> TopicOut:
    topic = Topic(name=body.name, slug=body.slug, description=body.description, color=body.color)
    db.add(topic)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe un tema con ese nombre o slug"
        ) from exc
    return _to_out(topic)


@router.put("/{topic_id}", response_model=TopicOut, dependencies=[Depends(require_csrf)])
def update_topic(topic_id: uuid.UUID, body: TopicUpdate, db: DbSession = Depends(get_db)) -> TopicOut:
    topic = _get_or_404(db, topic_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe un tema con ese nombre o slug"
        ) from exc
    return _to_out(topic)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def delete_topic(topic_id: uuid.UUID, db: DbSession = Depends(get_db)) -> None:
    topic = _get_or_404(db, topic_id)
    db.delete(topic)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede borrar: hay viajes o fotos que usan este tema",
        ) from exc
