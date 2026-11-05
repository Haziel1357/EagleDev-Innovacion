"""Controlador: reconocimiento del material de una foto y confirmación de la clasificación."""

from fastapi import APIRouter

router = APIRouter(prefix="/ia", tags=["Reconocimiento con IA"])
