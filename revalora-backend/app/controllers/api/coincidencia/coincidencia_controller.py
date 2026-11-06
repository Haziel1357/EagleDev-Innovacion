"""Controlador: coincidencias entre ofertas y necesidades."""

from fastapi import APIRouter

from app.core.database import DbSession
from app.schemas.coincidencia_schema import CoincidenciaResponse
from app.schemas.comun_schema import PaginaResponse
from app.security.usuario_autenticado import EmpresaActual
from app.services.coincidencia.motor_coincidencia_service import MotorCoincidenciaService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/coincidencias", tags=["Coincidencias"])


def _pagina(coincidencias, total, paginacion) -> PaginaResponse:
    return construir_pagina(
        [CoincidenciaResponse.model_validate(c) for c in coincidencias], total, paginacion
    )


@router.get("", response_model=PaginaResponse[CoincidenciaResponse])
def mis_coincidencias(
    empresa: EmpresaActual, db: DbSession, paginacion: PaginacionDep
) -> PaginaResponse:
    """Coincidencias de mis materiales y de mis necesidades, de mayor a menor puntuación."""
    coincidencias, total = MotorCoincidenciaService(db).de_empresa(
        empresa, paginacion.offset, paginacion.tamano
    )
    return _pagina(coincidencias, total, paginacion)


@router.get("/materiales/{material_id}", response_model=PaginaResponse[CoincidenciaResponse])
def coincidencias_de_material(
    material_id: int, empresa: EmpresaActual, db: DbSession, paginacion: PaginacionDep
) -> PaginaResponse:
    """Necesidades compatibles con uno de mis materiales."""
    coincidencias, total = MotorCoincidenciaService(db).de_material(
        empresa, material_id, paginacion.offset, paginacion.tamano
    )
    return _pagina(coincidencias, total, paginacion)


@router.get("/necesidades/{necesidad_id}", response_model=PaginaResponse[CoincidenciaResponse])
def coincidencias_de_necesidad(
    necesidad_id: int, empresa: EmpresaActual, db: DbSession, paginacion: PaginacionDep
) -> PaginaResponse:
    """Materiales compatibles con una de mis necesidades."""
    coincidencias, total = MotorCoincidenciaService(db).de_necesidad(
        empresa, necesidad_id, paginacion.offset, paginacion.tamano
    )
    return _pagina(coincidencias, total, paginacion)


@router.post("/materiales/{material_id}/recalcular", response_model=list[CoincidenciaResponse])
def recalcular_material(
    material_id: int, empresa: EmpresaActual, db: DbSession
) -> list[CoincidenciaResponse]:
    resultado = MotorCoincidenciaService(db).recalcular_para_material(empresa, material_id)
    return [CoincidenciaResponse.model_validate(c) for c in resultado]


@router.post("/necesidades/{necesidad_id}/recalcular", response_model=list[CoincidenciaResponse])
def recalcular_necesidad(
    necesidad_id: int, empresa: EmpresaActual, db: DbSession
) -> list[CoincidenciaResponse]:
    resultado = MotorCoincidenciaService(db).recalcular_para_necesidad(empresa, necesidad_id)
    return [CoincidenciaResponse.model_validate(c) for c in resultado]


@router.get("/{coincidencia_id}", response_model=CoincidenciaResponse)
def obtener_coincidencia(
    coincidencia_id: int, empresa: EmpresaActual, db: DbSession
) -> CoincidenciaResponse:
    return CoincidenciaResponse.model_validate(
        MotorCoincidenciaService(db).obtener(empresa, coincidencia_id)
    )
