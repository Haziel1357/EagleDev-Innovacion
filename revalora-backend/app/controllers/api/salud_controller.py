"""Controlador: verificación de que la API está activa."""

from fastapi import APIRouter

router = APIRouter(tags=["Salud"])


@router.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
