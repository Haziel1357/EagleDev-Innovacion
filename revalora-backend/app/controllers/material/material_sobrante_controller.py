"""Controlador: publicación, listado y detalle de materiales sobrantes."""

from fastapi import APIRouter

router = APIRouter(prefix="/materiales", tags=["Materiales"])
