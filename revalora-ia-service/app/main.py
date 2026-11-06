"""Punto de entrada del servicio de IA de REVALORA.

Ejecución en desarrollo:
    uv run uvicorn app.main:app --reload --port 8000
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router
from app.core.config import PREFIJO_API, Settings, settings
from app.core.errores import registrar_manejadores
from app.core.logging import configurar_logging
from app.ml.recomendacion.catalogo import obtener_catalogo
from app.ml.vision.clasificador_materiales import ProveedorClasificador


def crear_app(config: Settings = settings) -> FastAPI:
    configurar_logging(config.debug)

    @asynccontextmanager
    async def ciclo_de_vida(app: FastAPI) -> AsyncIterator[None]:
        obtener_catalogo()  # valida el catálogo: si el JSON tiene errores, no arranca
        app.state.proveedor_clasificador = ProveedorClasificador(config)
        if config.cargar_modelo_al_iniciar:
            app.state.proveedor_clasificador.obtener()
        yield

    app = FastAPI(
        title=config.nombre_app,
        description="Reconocimiento de materiales, recomendación de materiales y "
        "oportunidades productivas. Contrato: docs/contrato-api-ia.md.",
        version="0.1.0",
        debug=config.debug,
        lifespan=ciclo_de_vida,
    )
    registrar_manejadores(app)
    app.include_router(router, prefix=PREFIJO_API)
    return app


app = crear_app()
