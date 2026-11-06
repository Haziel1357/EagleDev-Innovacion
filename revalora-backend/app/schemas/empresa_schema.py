"""Esquemas Pydantic (entrada y salida) del módulo empresa."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.empresa.enums import TipoEmpresa
from app.schemas.comun_schema import EsquemaORM


class UbicacionSchema(EsquemaORM):
    direccion: str | None = Field(default=None, max_length=255)
    ciudad: str = Field(min_length=2, max_length=100)
    region: str | None = Field(default=None, max_length=100)
    pais: str = Field(default="Colombia", max_length=100)
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)


class ActividadEconomicaResponse(EsquemaORM):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None


class EmpresaRequest(BaseModel):
    nombre: str = Field(min_length=2, max_length=150)
    identificacion: str | None = Field(default=None, max_length=30, description="NIT o RUT.")
    tipo: TipoEmpresa
    descripcion: str | None = Field(default=None, max_length=2000)
    telefono: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    actividad_economica_id: int | None = None
    ubicacion: UbicacionSchema


class EmpresaResumenResponse(EsquemaORM):
    id: int
    nombre: str
    tipo: TipoEmpresa
    ubicacion: UbicacionSchema


class EmpresaResponse(EmpresaResumenResponse):
    usuario_id: int
    identificacion: str | None
    descripcion: str | None
    telefono: str | None
    email: str | None
    actividad_economica: ActividadEconomicaResponse | None
    creado_en: datetime
