"""Controlador: solicitudes de compra o intercambio."""

from fastapi import APIRouter, status

from app.core.database import DbSession
from app.models import EstadoSolicitud
from app.schemas.comun_schema import PaginaResponse
from app.schemas.transaccion_schema import (
    RespuestaSolicitudRequest,
    SolicitudRequest,
    SolicitudResponse,
)
from app.security.usuario_autenticado import EmpresaActual, UsuarioActual
from app.services.transaccion.solicitud_service import SolicitudService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/solicitudes", tags=["Transacciones"])


def _respuesta(solicitud) -> SolicitudResponse:
    return SolicitudResponse.model_validate(solicitud)


@router.post("", response_model=SolicitudResponse, status_code=status.HTTP_201_CREATED)
def crear_solicitud(
    datos: SolicitudRequest, usuario: UsuarioActual, empresa: EmpresaActual, db: DbSession
) -> SolicitudResponse:
    """Solicita un material: COMPRA (material en venta), INTERCAMBIO o APROVECHAMIENTO."""
    return _respuesta(SolicitudService(db).crear(usuario, empresa, datos))


@router.get("/enviadas", response_model=PaginaResponse[SolicitudResponse])
def solicitudes_enviadas(
    empresa: EmpresaActual,
    db: DbSession,
    paginacion: PaginacionDep,
    estado: EstadoSolicitud | None = None,
) -> PaginaResponse:
    solicitudes, total = SolicitudService(db).enviadas(
        empresa, estado, paginacion.offset, paginacion.tamano
    )
    return construir_pagina([_respuesta(s) for s in solicitudes], total, paginacion)


@router.get("/recibidas", response_model=PaginaResponse[SolicitudResponse])
def solicitudes_recibidas(
    empresa: EmpresaActual,
    db: DbSession,
    paginacion: PaginacionDep,
    estado: EstadoSolicitud | None = None,
) -> PaginaResponse:
    solicitudes, total = SolicitudService(db).recibidas(
        empresa, estado, paginacion.offset, paginacion.tamano
    )
    return construir_pagina([_respuesta(s) for s in solicitudes], total, paginacion)


@router.get("/{solicitud_id}", response_model=SolicitudResponse)
def obtener_solicitud(
    solicitud_id: int, empresa: EmpresaActual, db: DbSession
) -> SolicitudResponse:
    return _respuesta(SolicitudService(db).obtener(empresa, solicitud_id))


@router.post("/{solicitud_id}/aceptar", response_model=SolicitudResponse)
def aceptar_solicitud(
    solicitud_id: int,
    usuario: UsuarioActual,
    empresa: EmpresaActual,
    db: DbSession,
    datos: RespuestaSolicitudRequest | None = None,
) -> SolicitudResponse:
    """La empresa dueña del material acepta; se descuenta la cantidad del material."""
    comentario = datos.comentario if datos else None
    return _respuesta(SolicitudService(db).aceptar(usuario, empresa, solicitud_id, comentario))


@router.post("/{solicitud_id}/rechazar", response_model=SolicitudResponse)
def rechazar_solicitud(
    solicitud_id: int,
    usuario: UsuarioActual,
    empresa: EmpresaActual,
    db: DbSession,
    datos: RespuestaSolicitudRequest | None = None,
) -> SolicitudResponse:
    comentario = datos.comentario if datos else None
    return _respuesta(SolicitudService(db).rechazar(usuario, empresa, solicitud_id, comentario))


@router.post("/{solicitud_id}/cancelar", response_model=SolicitudResponse)
def cancelar_solicitud(
    solicitud_id: int,
    usuario: UsuarioActual,
    empresa: EmpresaActual,
    db: DbSession,
    datos: RespuestaSolicitudRequest | None = None,
) -> SolicitudResponse:
    """Quien envió la solicitud la retira mientras sigue pendiente."""
    comentario = datos.comentario if datos else None
    return _respuesta(SolicitudService(db).cancelar(usuario, empresa, solicitud_id, comentario))


@router.post("/{solicitud_id}/completar", response_model=SolicitudResponse)
def completar_solicitud(
    solicitud_id: int,
    usuario: UsuarioActual,
    empresa: EmpresaActual,
    db: DbSession,
    datos: RespuestaSolicitudRequest | None = None,
) -> SolicitudResponse:
    """Marca como realizada la entrega de una solicitud aceptada."""
    comentario = datos.comentario if datos else None
    return _respuesta(SolicitudService(db).completar(usuario, empresa, solicitud_id, comentario))
