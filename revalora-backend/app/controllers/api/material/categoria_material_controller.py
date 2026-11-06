"""Controlador: categorías de materiales."""

from fastapi import APIRouter, status

from app.core.database import DbSession
from app.schemas.material_schema import CategoriaMaterialRequest, CategoriaMaterialResponse
from app.security.usuario_autenticado import AdminActual
from app.services.material.categoria_material_service import CategoriaMaterialService

router = APIRouter(prefix="/categorias", tags=["Materiales"])


@router.get("", response_model=list[CategoriaMaterialResponse])
def listar_categorias(
    db: DbSession, incluir_inactivas: bool = False
) -> list[CategoriaMaterialResponse]:
    categorias = CategoriaMaterialService(db).listar(solo_activas=not incluir_inactivas)
    return [CategoriaMaterialResponse.model_validate(c) for c in categorias]


@router.get("/{categoria_id}", response_model=CategoriaMaterialResponse)
def obtener_categoria(categoria_id: int, db: DbSession) -> CategoriaMaterialResponse:
    return CategoriaMaterialResponse.model_validate(
        CategoriaMaterialService(db).obtener(categoria_id)
    )


@router.post("", response_model=CategoriaMaterialResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    datos: CategoriaMaterialRequest, _: AdminActual, db: DbSession
) -> CategoriaMaterialResponse:
    """Solo administradores."""
    return CategoriaMaterialResponse.model_validate(CategoriaMaterialService(db).crear(datos))


@router.put("/{categoria_id}", response_model=CategoriaMaterialResponse)
def actualizar_categoria(
    categoria_id: int, datos: CategoriaMaterialRequest, _: AdminActual, db: DbSession
) -> CategoriaMaterialResponse:
    """Solo administradores."""
    return CategoriaMaterialResponse.model_validate(
        CategoriaMaterialService(db).actualizar(categoria_id, datos)
    )
