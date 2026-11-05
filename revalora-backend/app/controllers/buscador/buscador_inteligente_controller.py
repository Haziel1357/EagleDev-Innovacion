"""Controlador: buscador inteligente a partir de lo que el usuario quiere fabricar."""

from fastapi import APIRouter

from app.core.database import DbSession
from app.schemas.buscador_schema import (
    BusquedaFabricacionRequest,
    BusquedaHistorialResponse,
    ResultadoBusquedaResponse,
)
from app.schemas.comun_schema import PaginaResponse
from app.security.usuario_autenticado import UsuarioActual
from app.services.buscador.buscador_inteligente_service import BuscadorInteligenteService
from app.services.ia.ia_service_client import IaClientDep
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/buscador/inteligente", tags=["Buscador"])


@router.post("", response_model=ResultadoBusquedaResponse)
def buscar_por_producto(
    datos: BusquedaFabricacionRequest, usuario: UsuarioActual, db: DbSession, ia: IaClientDep
) -> ResultadoBusquedaResponse:
    """Describe lo que quieres fabricar y recibe los materiales disponibles que te sirven.

    La IA deduce los materiales necesarios; por cada uno se listan las publicaciones
    disponibles ordenadas por estado, cercanía, cantidad y precio.
    """
    return BuscadorInteligenteService(db, ia).buscar(usuario, datos)


@router.get("/historial", response_model=PaginaResponse[BusquedaHistorialResponse])
def historial_busquedas(
    usuario: UsuarioActual, db: DbSession, ia: IaClientDep, paginacion: PaginacionDep
) -> PaginaResponse:
    busquedas, total = BuscadorInteligenteService(db, ia).historial(
        usuario, paginacion.offset, paginacion.tamano
    )
    return construir_pagina(
        [BusquedaHistorialResponse.model_validate(b) for b in busquedas], total, paginacion
    )


@router.get("/historial/{busqueda_id}", response_model=BusquedaHistorialResponse)
def obtener_busqueda(
    busqueda_id: int, usuario: UsuarioActual, db: DbSession, ia: IaClientDep
) -> BusquedaHistorialResponse:
    return BusquedaHistorialResponse.model_validate(
        BuscadorInteligenteService(db, ia).obtener(usuario, busqueda_id)
    )
