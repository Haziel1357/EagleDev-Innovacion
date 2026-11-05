"""Manejadores globales de errores.

Responden con una página HTML (templates/error/) cuando la petición viene del
navegador y con JSON (ErrorResponse) en el resto de casos.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.web import templates
from app.exceptions.errores import RevaloraError
from app.schemas.comun_schema import ErrorResponse

logger = logging.getLogger(__name__)

_PAGINAS_ERROR = {404, 500}


def _responder(
    request: Request, estado: int, mensaje: str, detalles: list[dict] | None = None
) -> Response:
    if estado in _PAGINAS_ERROR and "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(
            request, f"error/{estado}.html", {"mensaje": mensaje}, status_code=estado
        )
    cuerpo = ErrorResponse(
        estado=estado,
        error=HTTPStatus(estado).phrase,
        mensaje=mensaje,
        ruta=request.url.path,
        detalles=detalles,
    )
    cabeceras = {"WWW-Authenticate": "Bearer"} if estado == 401 else None
    return JSONResponse(
        jsonable_encoder(cuerpo, exclude_none=True), status_code=estado, headers=cabeceras
    )


async def _error_revalora(request: Request, exc: RevaloraError) -> Response:
    return _responder(request, exc.estado_http, exc.mensaje)


async def _error_http(request: Request, exc: StarletteHTTPException) -> Response:
    return _responder(request, exc.status_code, str(exc.detail))


async def _error_validacion(request: Request, exc: RequestValidationError) -> Response:
    detalles = [
        {
            "campo": ".".join(str(parte) for parte in error.get("loc", ())),
            "mensaje": error.get("msg", ""),
        }
        for error in exc.errors()
    ]
    return _responder(request, 422, "Los datos enviados no son válidos.", detalles)


async def _error_inesperado(request: Request, exc: Exception) -> Response:
    logger.exception("Error no controlado en %s", request.url.path)
    return _responder(request, 500, "Error interno del servidor.")


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(RevaloraError, _error_revalora)
    app.add_exception_handler(StarletteHTTPException, _error_http)
    app.add_exception_handler(RequestValidationError, _error_validacion)
    app.add_exception_handler(Exception, _error_inesperado)
