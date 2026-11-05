"""Controlador: registro y consulta de empresas."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.database import DbSession
from app.models import TipoEmpresa
from app.schemas.comun_schema import PaginaResponse
from app.schemas.empresa_schema import ActividadEconomicaResponse, EmpresaRequest, EmpresaResponse
from app.security.usuario_autenticado import EmpresaActual, UsuarioActual
from app.services.empresa.empresa_service import EmpresaService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/empresas", tags=["Empresas"])


@router.get("/actividades", response_model=list[ActividadEconomicaResponse])
def listar_actividades(db: DbSession) -> list[ActividadEconomicaResponse]:
    """Catálogo de actividades económicas."""
    return [
        ActividadEconomicaResponse.model_validate(a)
        for a in EmpresaService(db).listar_actividades()
    ]


@router.post("", response_model=EmpresaResponse, status_code=status.HTTP_201_CREATED)
def registrar_empresa(
    datos: EmpresaRequest, usuario: UsuarioActual, db: DbSession
) -> EmpresaResponse:
    """Registra la empresa del usuario autenticado (una por cuenta)."""
    return EmpresaResponse.model_validate(EmpresaService(db).registrar(usuario, datos))


@router.get("/mia", response_model=EmpresaResponse)
def mi_empresa(empresa: EmpresaActual) -> EmpresaResponse:
    return EmpresaResponse.model_validate(empresa)


@router.get("", response_model=PaginaResponse[EmpresaResponse])
def listar_empresas(
    db: DbSession,
    paginacion: PaginacionDep,
    texto: Annotated[str | None, Query(max_length=100)] = None,
    tipo: TipoEmpresa | None = None,
    ciudad: Annotated[str | None, Query(max_length=100)] = None,
    actividad_economica_id: int | None = None,
) -> PaginaResponse:
    empresas, total = EmpresaService(db).buscar(
        texto=texto,
        tipo=tipo,
        ciudad=ciudad,
        actividad_economica_id=actividad_economica_id,
        offset=paginacion.offset,
        limite=paginacion.tamano,
    )
    return construir_pagina(
        [EmpresaResponse.model_validate(e) for e in empresas], total, paginacion
    )


@router.get("/{empresa_id}", response_model=EmpresaResponse)
def obtener_empresa(empresa_id: int, db: DbSession) -> EmpresaResponse:
    return EmpresaResponse.model_validate(EmpresaService(db).obtener(empresa_id))


@router.put("/{empresa_id}", response_model=EmpresaResponse)
def actualizar_empresa(
    empresa_id: int, datos: EmpresaRequest, usuario: UsuarioActual, db: DbSession
) -> EmpresaResponse:
    return EmpresaResponse.model_validate(EmpresaService(db).actualizar(usuario, empresa_id, datos))
