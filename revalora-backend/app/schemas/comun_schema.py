"""Esquemas genéricos de respuesta compartidos por todos los módulos."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    exito: bool = True
    mensaje: str | None = None
    datos: T | None = None


class PaginaResponse(BaseModel, Generic[T]):
    elementos: list[T]
    total: int
    pagina: int
    tamano: int


class ErrorResponse(BaseModel):
    estado: int
    error: str
    mensaje: str
    ruta: str
