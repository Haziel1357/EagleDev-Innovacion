"""Autenticación: registro, inicio de sesión y emisión de tokens."""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.exceptions import NoAutenticadoError, ReglaNegocioError
from app.models import Usuario
from app.repositories.usuario.rol_repository import RolRepository
from app.repositories.usuario.usuario_repository import UsuarioRepository
from app.schemas.usuario_schema import AuthResponse, RegistroUsuarioRequest, UsuarioResponse
from app.security.password import hashear_password, verificar_password
from app.security.tokens import crear_token_acceso
from app.utils.constantes import ROL_EMPRESA


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.usuarios = UsuarioRepository(db)
        self.roles = RolRepository(db)

    def registrar(self, datos: RegistroUsuarioRequest) -> AuthResponse:
        email = datos.email.lower()
        if self.usuarios.existe_email(email):
            raise ReglaNegocioError("Ya existe una cuenta con ese correo.")

        rol = self.roles.por_nombre(ROL_EMPRESA)
        if rol is None:
            raise ReglaNegocioError("Los roles no están configurados. Ejecuta las migraciones.")

        usuario = self.usuarios.agregar(
            Usuario(
                nombre=datos.nombre.strip(),
                email=email,
                password_hash=hashear_password(datos.password),
                telefono=datos.telefono,
                rol=rol,
            )
        )
        self.db.commit()
        return self._respuesta(usuario)

    def autenticar(self, email: str, password: str) -> AuthResponse:
        usuario = self.usuarios.por_email(email)
        if usuario is None or not verificar_password(password, usuario.password_hash):
            raise NoAutenticadoError("Correo o contraseña incorrectos.")
        if not usuario.activo:
            raise NoAutenticadoError("La cuenta está desactivada.")
        return self._respuesta(usuario)

    @staticmethod
    def _respuesta(usuario: Usuario) -> AuthResponse:
        return AuthResponse(
            access_token=crear_token_acceso(usuario.id),
            expira_en=settings.access_token_expire_minutes * 60,
            usuario=UsuarioResponse.model_validate(usuario),
        )
