"""Controlador: historial de operaciones."""

from fastapi import APIRouter

from app.core.database import DbSession
from app.schemas.comun_schema import PaginaResponse
from app.schemas.transaccion_schema import HistorialOperacionResponse
from app.security.usuario_autenticado import EmpresaActual
from app.services.transaccion.historial_operacion_service import HistorialOperacionService
from app.services.transaccion.solicitud_service import SolicitudService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/historial", tags=["Transacciones"])


@router.get("", response_model=PaginaResponse[HistorialOperacionResponse])
def mi_historial(
    empresa: EmpresaActual, db: DbSession, paginacion: PaginacionDep
) -> PaginaResponse:
    """Todas las operaciones de las solicitudes en las que participa mi empresa."""
    entradas, total = HistorialOperacionService(db).de_empresa(
        empresa, paginacion.offset, paginacion.tamano
    )
    return construir_pagina(
        [HistorialOperacionResponse.model_validate(e) for e in entradas], total, paginacion
    )


@router.get("/solicitudes/{solicitud_id}", response_model=list[HistorialOperacionResponse])
def historial_de_solicitud(
    solicitud_id: int, empresa: EmpresaActual, db: DbSession
) -> list[HistorialOperacionResponse]:
    solicitud = SolicitudService(db).obtener(empresa, solicitud_id)
    return [HistorialOperacionResponse.model_validate(e) for e in solicitud.historial]
