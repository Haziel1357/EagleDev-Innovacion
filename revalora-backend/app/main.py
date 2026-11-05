"""Punto de entrada del backend de REVALORA.

Ejecución en desarrollo:
    uvicorn app.main:app --reload --port 8080
"""

from fastapi import FastAPI

from app.controllers.router import router
from app.core.config import settings
from app.core.logging import configurar_logging
from app.core.web import montar_archivos
from app.exceptions.handlers import registrar_manejadores


def crear_app() -> FastAPI:
    configurar_logging(settings.debug)

    app = FastAPI(title=settings.nombre_app, debug=settings.debug)
    montar_archivos(app)
    registrar_manejadores(app)
    app.include_router(router)
    return app


app = crear_app()
