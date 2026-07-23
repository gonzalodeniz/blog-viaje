"""Punto de entrada de la API FastAPI."""

from fastapi import FastAPI

from app.api.admin_photos import router as admin_photos_router
from app.api.admin_topics import router as admin_topics_router
from app.api.admin_trips import router as admin_trips_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.photos import router as photos_router
from app.api.trips import router as trips_router

app = FastAPI(title="Bitácora API")
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(trips_router)
app.include_router(photos_router)
app.include_router(admin_topics_router)
app.include_router(admin_trips_router)
app.include_router(admin_photos_router)
