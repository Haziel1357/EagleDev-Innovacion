"""Reúne los endpoints de la versión 1 de la API (prefijo /api/v1, en main.py)."""

from fastapi import APIRouter

from app.api.v1.endpoints import oportunidades, recomendacion, reconocimiento, salud

router = APIRouter()
for endpoint in (salud, reconocimiento, recomendacion, oportunidades):
    router.include_router(endpoint.router)
