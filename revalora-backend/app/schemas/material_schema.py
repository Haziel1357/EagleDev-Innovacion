"""Esquemas Pydantic (entrada y salida) del módulo material."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.material.enums import (
    DisponibilidadMaterial,
    EstadoMaterial,
    TipoOferta,
    UnidadMedida,
)
from app.schemas.comun_schema import EsquemaORM
from app.schemas.empresa_schema import EmpresaResumenResponse


class CategoriaMaterialRequest(BaseModel):
    codigo: str = Field(min_length=2, max_length=40, pattern=r"^[a-z0-9_]+$")
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str | None = Field(default=None, max_length=300)
    activa: bool = True


class CategoriaMaterialResponse(EsquemaORM):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None
    activa: bool


class DimensionesSchema(EsquemaORM):
    """Medidas en centímetros. Todas son opcionales."""

    largo_cm: float | None = Field(default=None, gt=0)
    ancho_cm: float | None = Field(default=None, gt=0)
    alto_cm: float | None = Field(default=None, gt=0)


class MaterialSobranteRequest(BaseModel):
    categoria_id: int
    titulo: str = Field(min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    cantidad: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unidad_medida: UnidadMedida
    estado: EstadoMaterial
    tipo_oferta: TipoOferta
    precio: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    dimensiones: DimensionesSchema | None = None
    clasificacion_id: int | None = Field(
        default=None,
        description="Reconocimiento con IA (POST /ia/reconocimiento) de la foto del material. "
        "Si se indica, la foto se añade como principal y el material queda verificado.",
    )

    @model_validator(mode="after")
    def _precio_segun_oferta(self) -> "MaterialSobranteRequest":
        if self.tipo_oferta == TipoOferta.VENTA and self.precio is None:
            raise ValueError("Un material en venta debe tener precio.")
        if self.tipo_oferta == TipoOferta.APROVECHAMIENTO:
            self.precio = None
        return self


class DisponibilidadRequest(BaseModel):
    disponibilidad: DisponibilidadMaterial


class FiltroMaterialRequest(BaseModel):
    """Filtros de búsqueda de materiales (se reciben como parámetros de la URL)."""

    texto: str | None = Field(
        default=None, max_length=100, description="Busca en título y descripción."
    )
    categoria_id: int | None = None
    categoria_codigo: str | None = Field(default=None, max_length=40)
    estado_minimo: EstadoMaterial | None = None
    tipo_oferta: TipoOferta | None = None
    precio_maximo: Decimal | None = Field(default=None, ge=0)
    ciudad: str | None = Field(default=None, max_length=100)
    solo_verificados: bool = False
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    radio_km: float | None = Field(
        default=None,
        gt=0,
        le=1000,
        description="Requiere latitud y longitud (o, en la búsqueda tradicional con sesión, "
        "se usa la ubicación de tu empresa).",
    )

    @property
    def coordenadas(self) -> tuple[float, float] | None:
        if self.latitud is None or self.longitud is None:
            return None
        return (self.latitud, self.longitud)


class FotoMaterialResponse(EsquemaORM):
    id: int
    url: str
    nombre_original: str | None
    tipo_mime: str
    tamano_bytes: int
    es_principal: bool


class MaterialSobranteResponse(EsquemaORM):
    id: int
    titulo: str
    descripcion: str | None
    categoria: CategoriaMaterialResponse
    cantidad: Decimal
    unidad_medida: UnidadMedida
    estado: EstadoMaterial
    tipo_oferta: TipoOferta
    precio: Decimal | None
    disponibilidad: DisponibilidadMaterial
    verificado_ia: bool
    dimensiones: DimensionesSchema
    empresa: EmpresaResumenResponse
    fotos: list[FotoMaterialResponse]
    distancia_km: float | None = Field(
        default=None, description="Distancia al punto de búsqueda, si se indicó."
    )
    creado_en: datetime
    actualizado_en: datetime
