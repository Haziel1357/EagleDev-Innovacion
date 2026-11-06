"""Controlador: publicación y consulta de necesidades de materiales."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.database import DbSession
from app.models import EstadoNecesidad
from app.schemas.comun_schema import PaginaResponse
from app.schemas.necesidad_schema import (
    EstadoNecesidadRequest,
    NecesidadMaterialRequest,
    NecesidadMaterialResponse,
)
from app.security.usuario_autenticado import EmpresaActual
from app.services.necesidad.necesidad_material_service import NecesidadMaterialService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/necesidades", tags=["Necesidades"])


def _respuesta(necesidad) -> NecesidadMaterialResponse:
    return NecesidadMaterialResponse.model_validate(necesidad)


@router.get("", response_model=PaginaResponse[NecesidadMaterialResponse])
def listar_necesidades(
    db: DbSession,
    paginacion: PaginacionDep,
    texto: Annotated[str | None, Query(max_length=100)] = None,
    categoria_id: int | None = None,
    estado: EstadoNecesidad | None = EstadoNecesidad.ABIERTA,
) -> PaginaResponse:
    necesidades, total = NecesidadMaterialService(db).buscar(
        texto=texto,
        categoria_id=categoria_id,
        estado=estado,
        offset=paginacion.offset,
        limite=paginacion.tamano,
    )
    return construir_pagina([_respuesta(n) for n in necesidades], total, paginacion)


@router.get("/mias", response_model=PaginaResponse[NecesidadMaterialResponse])
def mis_necesidades(
    empresa: EmpresaActual,
    db: DbSession,
    paginacion: PaginacionDep,
    estado: EstadoNecesidad | None = None,
) -> PaginaResponse:
    necesidades, total = NecesidadMaterialService(db).buscar(
        texto=None,
        categoria_id=None,
        estado=estado,
        empresa_id=empresa.id,
        offset=paginacion.offset,
        limite=paginacion.tamano,
    )
    return construir_pagina([_respuesta(n) for n in necesidades], total, paginacion)


@router.post("", response_model=NecesidadMaterialResponse, status_code=status.HTTP_201_CREATED)
def publicar_necesidad(
    datos: NecesidadMaterialRequest, empresa: EmpresaActual, db: DbSession
) -> NecesidadMaterialResponse:
    """Publica una necesidad y calcula de inmediato sus coincidencias con los materiales disponibles."""
    return _respuesta(NecesidadMaterialService(db).publicar(empresa, datos))


@router.get("/{necesidad_id}", response_model=NecesidadMaterialResponse)
def obtener_necesidad(necesidad_id: int, db: DbSession) -> NecesidadMaterialResponse:
    return _respuesta(NecesidadMaterialService(db).obtener(necesidad_id))


@router.put("/{necesidad_id}", response_model=NecesidadMaterialResponse)
def actualizar_necesidad(
    necesidad_id: int, datos: NecesidadMaterialRequest, empresa: EmpresaActual, db: DbSession
) -> NecesidadMaterialResponse:
    return _respuesta(NecesidadMaterialService(db).actualizar(empresa, necesidad_id, datos))


@router.patch("/{necesidad_id}/estado", response_model=NecesidadMaterialResponse)
def cambiar_estado_necesidad(
    necesidad_id: int, datos: EstadoNecesidadRequest, empresa: EmpresaActual, db: DbSession
) -> NecesidadMaterialResponse:
    return _respuesta(
        NecesidadMaterialService(db).cambiar_estado(empresa, necesidad_id, datos.estado)
    )


@router.delete("/{necesidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_necesidad(necesidad_id: int, empresa: EmpresaActual, db: DbSession) -> None:
    """Cierra la necesidad (se conserva el registro)."""
    NecesidadMaterialService(db).cambiar_estado(empresa, necesidad_id, EstadoNecesidad.CERRADA)
