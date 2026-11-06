"""Controlador: oportunidades productivas."""

from fastapi import APIRouter, status

from app.core.database import DbSession
from app.schemas.comun_schema import PaginaResponse
from app.schemas.oportunidad_schema import AnalisisOportunidadRequest, OportunidadProductivaResponse
from app.security.usuario_autenticado import EmpresaActual
from app.services.ia.ia_service_client import IaClientDep
from app.services.oportunidad.oportunidad_productiva_service import OportunidadProductivaService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/oportunidades", tags=["Oportunidades"])


@router.post(
    "/analizar", response_model=OportunidadProductivaResponse, status_code=status.HTTP_201_CREATED
)
def analizar_oportunidades(
    datos: AnalisisOportunidadRequest, empresa: EmpresaActual, db: DbSession, ia: IaClientDep
) -> OportunidadProductivaResponse:
    """Sugiere productos que puedes fabricar con tus materiales e indica cuáles te faltan."""
    return OportunidadProductivaResponse.model_validate(
        OportunidadProductivaService(db, ia).analizar(empresa, datos)
    )


@router.get("", response_model=PaginaResponse[OportunidadProductivaResponse])
def mis_oportunidades(
    empresa: EmpresaActual, db: DbSession, ia: IaClientDep, paginacion: PaginacionDep
) -> PaginaResponse:
    oportunidades, total = OportunidadProductivaService(db, ia).de_empresa(
        empresa, paginacion.offset, paginacion.tamano
    )
    return construir_pagina(
        [OportunidadProductivaResponse.model_validate(o) for o in oportunidades], total, paginacion
    )


@router.get("/{oportunidad_id}", response_model=OportunidadProductivaResponse)
def obtener_oportunidad(
    oportunidad_id: int, empresa: EmpresaActual, db: DbSession, ia: IaClientDep
) -> OportunidadProductivaResponse:
    return OportunidadProductivaResponse.model_validate(
        OportunidadProductivaService(db, ia).obtener(empresa, oportunidad_id)
    )
