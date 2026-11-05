"""Controlador: registro, inicio y cierre de sesión."""

from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Autenticación"])
