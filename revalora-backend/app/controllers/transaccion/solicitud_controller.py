"""Controlador: solicitudes de compra o intercambio."""

from fastapi import APIRouter

router = APIRouter(prefix="/solicitudes", tags=["Transacciones"])
