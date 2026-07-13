"""Punto de entrada de la API FastAPI."""

from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="Bitácora API")
app.include_router(health_router)
