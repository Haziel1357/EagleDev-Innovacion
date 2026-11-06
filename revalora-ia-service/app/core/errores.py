"""Errores del servicio y manejadores globales.

Las respuestas de error usan el mismo formato que el backend:
``{"estado", "error", "mensaje", "ruta", "detalles"?}``.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ServicioIaError(Exception):
    """Error base del servicio. Cada subclase define su código HTTP."""

    estado_http: int = 500

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje


class ImagenInvalidaError(ServicioIaError):
    """El archivo no es una imagen JPG, PNG o WEBP válida."""

    estado_http = 400


class ImagenDemasiadoGrandeError(ServicioIaError):
    estado_http = 413


class ModeloNoDisponibleError(ServicioIaError):
    """El modelo de visión no se pudo cargar."""

    estado_http = 503


def _responder(
    request: Request, estado: int, mensaje: str, detalles: list[dict] | None = None
) -> JSONResponse:
    cuerpo = {
        "estado": estado,
        "error": HTTPStatus(estado).phrase,
        "mensaje": mensaje,
        "ruta": request.url.path,
    }
    if detalles:
        cuerpo["detalles"] = detalles
    return JSONResponse(cuerpo, status_code=estado)


async def _error_servicio(request: Request, exc: ServicioIaError) -> JSONResponse:
    return _responder(request, exc.estado_http, exc.mensaje)


async def _error_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _responder(request, exc.status_code, str(exc.detail))


async def _error_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    detalles = [
        {
            "campo": ".".join(str(parte) for parte in error.get("loc", ())),
            "mensaje": error.get("msg", ""),
        }
        for error in exc.errors()
    ]
    return _responder(request, 422, "Los datos enviados no son válidos.", detalles)


async def _error_inesperado(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s", request.url.path)
    return _responder(request, 500, "Error interno del servicio de IA.")


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(ServicioIaError, _error_servicio)
    app.add_exception_handler(StarletteHTTPException, _error_http)
    app.add_exception_handler(RequestValidationError, _error_validacion)
    app.add_exception_handler(Exception, _error_inesperado)
