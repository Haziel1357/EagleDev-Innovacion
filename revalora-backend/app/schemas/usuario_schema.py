"""Esquemas Pydantic (entrada y salida) del módulo usuario."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.comun_schema import EsquemaORM


class RegistroUsuarioRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telefono: str | None = Field(default=None, max_length=30)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ActualizarPerfilRequest(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    telefono: str | None = Field(default=None, max_length=30)
    password_actual: str | None = Field(default=None, max_length=128)
    password_nueva: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def _cambio_password_completo(self) -> "ActualizarPerfilRequest":
        if self.password_nueva and not self.password_actual:
            raise ValueError("Para cambiar la contraseña indica también la contraseña actual.")
        return self


class UsuarioResponse(EsquemaORM):
    id: int
    nombre: str
    email: str
    telefono: str | None
    activo: bool
    rol: str = Field(validation_alias="rol_nombre")
    empresa_id: int | None
    creado_en: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en: int = Field(description="Segundos de validez del token.")
    usuario: UsuarioResponse
