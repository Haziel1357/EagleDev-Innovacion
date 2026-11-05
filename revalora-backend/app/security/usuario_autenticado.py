"""Dependencias de FastAPI que obtienen el usuario autenticado de la petición.

El token se lee de la cabecera ``Authorization: Bearer <token>`` (clientes de la API
y Swagger) o, si no está, de la cookie ``access_token`` (vistas del navegador).
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer

from app.core.database import DbSession
from app.exceptions import AccesoDenegadoError, NoAutenticadoError, ReglaNegocioError
from app.models import Empresa, Usuario
from app.security.tokens import leer_usuario_id

COOKIE_TOKEN = "access_token"

_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def _token_de_peticion(
    request: Request, token_cabecera: Annotated[str | None, Depends(_oauth2)]
) -> str | None:
    return token_cabecera or request.cookies.get(COOKIE_TOKEN)


def obtener_usuario_opcional(
    db: DbSession, token: Annotated[str | None, Depends(_token_de_peticion)]
) -> Usuario | None:
    """Usuario autenticado, o None si la petición no trae token."""
    if not token:
        return None
    usuario = db.get(Usuario, leer_usuario_id(token))
    if usuario is None or not usuario.activo:
        raise NoAutenticadoError("El usuario no existe o está inactivo.")
    return usuario


def obtener_usuario_actual(
    usuario: Annotated[Usuario | None, Depends(obtener_usuario_opcional)],
) -> Usuario:
    if usuario is None:
        raise NoAutenticadoError("Debes iniciar sesión.")
    return usuario


def requerir_admin(usuario: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Usuario:
    if not usuario.es_admin:
        raise AccesoDenegadoError("Solo un administrador puede realizar esta acción.")
    return usuario


def obtener_empresa_actual(usuario: Annotated[Usuario, Depends(obtener_usuario_actual)]) -> Empresa:
    """Empresa del usuario autenticado. Las publicaciones y solicitudes se hacen a su nombre."""
    if usuario.empresa is None:
        raise ReglaNegocioError("Primero registra los datos de tu empresa.")
    return usuario.empresa


UsuarioActual = Annotated[Usuario, Depends(obtener_usuario_actual)]
UsuarioOpcional = Annotated[Usuario | None, Depends(obtener_usuario_opcional)]
AdminActual = Annotated[Usuario, Depends(requerir_admin)]
EmpresaActual = Annotated[Empresa, Depends(obtener_empresa_actual)]
