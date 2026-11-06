"""Controlador: registro, inicio y cierre de sesión."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.database import DbSession
from app.schemas.usuario_schema import AuthResponse, LoginRequest, RegistroUsuarioRequest
from app.security.usuario_autenticado import COOKIE_TOKEN
from app.services.usuario.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _guardar_cookie(response: Response, auth: AuthResponse) -> None:
    """La cookie permite que las vistas HTML usen la sesión sin manejar el token en JS."""
    response.set_cookie(
        COOKIE_TOKEN,
        auth.access_token,
        max_age=auth.expira_en,
        httponly=True,
        samesite="lax",
        secure=settings.entorno == "prod",
    )


@router.post("/registro", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def registrar(datos: RegistroUsuarioRequest, db: DbSession, response: Response) -> AuthResponse:
    """Crea una cuenta y devuelve el token de sesión."""
    auth = AuthService(db).registrar(datos)
    _guardar_cookie(response, auth)
    return auth


@router.post("/login", response_model=AuthResponse)
def iniciar_sesion(datos: LoginRequest, db: DbSession, response: Response) -> AuthResponse:
    auth = AuthService(db).autenticar(datos.email, datos.password)
    _guardar_cookie(response, auth)
    return auth


@router.post("/token", response_model=AuthResponse, include_in_schema=True)
def token_oauth2(
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> AuthResponse:
    """Inicio de sesión con formulario OAuth2 (lo usa el botón *Authorize* de /docs).

    En `username` va el correo electrónico.
    """
    return AuthService(db).autenticar(formulario.username, formulario.password)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def cerrar_sesion(response: Response) -> Response:
    """Borra la cookie de sesión. Los clientes que usan la cabecera deben descartar su token."""
    response.status_code = status.HTTP_204_NO_CONTENT
    response.delete_cookie(COOKIE_TOKEN)
    return response
