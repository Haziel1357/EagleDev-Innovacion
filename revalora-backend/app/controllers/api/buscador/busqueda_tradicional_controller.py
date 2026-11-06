"""Controlador: búsqueda tradicional de materiales por filtros."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.core.database import DbSession
from app.schemas.buscador_schema import BusquedaTradicionalRequest
from app.schemas.comun_schema import PaginaResponse
from app.schemas.material_schema import MaterialSobranteResponse
from app.security.usuario_autenticado import UsuarioOpcional
from app.services.buscador.busqueda_tradicional_service import BusquedaTradicionalService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/buscador/tradicional", tags=["Buscador"])


@router.get("", response_model=PaginaResponse[MaterialSobranteResponse])
def buscar_materiales(
    filtro: Annotated[BusquedaTradicionalRequest, Query()],
    usuario: UsuarioOpcional,
    db: DbSession,
    paginacion: PaginacionDep,
) -> PaginaResponse:
    """Filtra los materiales disponibles por texto, categoría, estado, tipo de oferta,
    precio, ciudad y radio de distancia.

    Si hay sesión y no se envían coordenadas, se usa la ubicación de tu empresa para
    calcular la distancia, y tus propios materiales no aparecen en los resultados.
    """
    materiales, total = BusquedaTradicionalService(db).buscar(
        filtro, usuario, paginacion.offset, paginacion.tamano
    )
    return construir_pagina(
        [MaterialSobranteResponse.model_validate(m) for m in materiales], total, paginacion
    )
