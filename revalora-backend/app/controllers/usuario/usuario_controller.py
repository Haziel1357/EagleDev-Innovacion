"""Controlador: perfil del usuario."""

from fastapi import APIRouter

from app.core.database import DbSession
from app.schemas.comun_schema import PaginaResponse
from app.schemas.usuario_schema import ActualizarPerfilRequest, UsuarioResponse
from app.security.usuario_autenticado import AdminActual, UsuarioActual
from app.services.usuario.usuario_service import UsuarioService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/me", response_model=UsuarioResponse)
def mi_perfil(usuario: UsuarioActual) -> UsuarioResponse:
    return UsuarioResponse.model_validate(usuario)


@router.put("/me", response_model=UsuarioResponse)
def actualizar_mi_perfil(
    datos: ActualizarPerfilRequest, usuario: UsuarioActual, db: DbSession
) -> UsuarioResponse:
    """Actualiza nombre y teléfono, o cambia la contraseña (indicando la actual)."""
    return UsuarioResponse.model_validate(UsuarioService(db).actualizar_perfil(usuario, datos))


@router.get("", response_model=PaginaResponse[UsuarioResponse])
def listar_usuarios(_: AdminActual, db: DbSession, paginacion: PaginacionDep) -> PaginaResponse:
    """Solo administradores."""
    usuarios, total = UsuarioService(db).listar(paginacion.offset, paginacion.tamano)
    return construir_pagina(
        [UsuarioResponse.model_validate(u) for u in usuarios], total, paginacion
    )


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, _: AdminActual, db: DbSession) -> UsuarioResponse:
    """Solo administradores."""
    return UsuarioResponse.model_validate(UsuarioService(db).obtener(usuario_id))


@router.patch("/{usuario_id}/activo", response_model=UsuarioResponse)
def cambiar_estado_usuario(
    usuario_id: int, activo: bool, _: AdminActual, db: DbSession
) -> UsuarioResponse:
    """Activa o desactiva una cuenta. Solo administradores."""
    return UsuarioResponse.model_validate(UsuarioService(db).cambiar_estado(usuario_id, activo))
