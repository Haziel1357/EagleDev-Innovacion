"""Gestión de perfiles de usuario."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontradoError, ReglaNegocioError
from app.models import Usuario
from app.repositories.usuario.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import ActualizarPerfilRequest
from app.security.password import hashear_password, verificar_password


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.usuarios = UsuarioRepository(db)

    def obtener(self, usuario_id: int) -> Usuario:
        usuario = self.usuarios.obtener(usuario_id)
        if usuario is None:
            raise RecursoNoEncontradoError("Usuario no encontrado.")
        return usuario

    def listar(self, offset: int, limite: int) -> tuple[Sequence[Usuario], int]:
        return self.usuarios.listar_paginado(offset, limite)

    def actualizar_perfil(self, usuario: Usuario, datos: ActualizarPerfilRequest) -> Usuario:
        if datos.nombre is not None:
            usuario.nombre = datos.nombre.strip()
        if "telefono" in datos.model_fields_set:
            usuario.telefono = datos.telefono
        if datos.password_nueva:
            if not verificar_password(datos.password_actual or "", usuario.password_hash):
                raise ReglaNegocioError("La contraseña actual no es correcta.")
            usuario.password_hash = hashear_password(datos.password_nueva)
        self.db.commit()
        return usuario

    def cambiar_estado(self, usuario_id: int, activo: bool) -> Usuario:
        usuario = self.obtener(usuario_id)
        usuario.activo = activo
        self.db.commit()
        return usuario
