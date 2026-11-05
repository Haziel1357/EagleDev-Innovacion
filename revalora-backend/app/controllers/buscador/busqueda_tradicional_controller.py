"""Controlador: búsqueda tradicional de materiales por filtros."""

from fastapi import APIRouter

router = APIRouter(prefix="/buscador/tradicional", tags=["Buscador"])
