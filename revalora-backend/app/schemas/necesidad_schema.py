"""Esquemas Pydantic (entrada y salida) del módulo necesidad."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.material.enums import EstadoMaterial, UnidadMedida
from app.models.necesidad.enums import EstadoNecesidad
from app.schemas.comun_schema import EsquemaORM
from app.schemas.empresa_schema import EmpresaResumenResponse
from app.schemas.material_schema import CategoriaMaterialResponse, DimensionesSchema


class NecesidadMaterialRequest(BaseModel):
    categoria_id: int
    titulo: str = Field(min_length=3, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    cantidad: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    unidad_medida: UnidadMedida
    estado_minimo: EstadoMaterial = EstadoMaterial.REGULAR
    presupuesto_maximo: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    dimensiones_minimas: DimensionesSchema | None = None


class EstadoNecesidadRequest(BaseModel):
    estado: EstadoNecesidad


class NecesidadMaterialResponse(EsquemaORM):
    id: int
    titulo: str
    descripcion: str | None
    categoria: CategoriaMaterialResponse
    cantidad: Decimal
    unidad_medida: UnidadMedida
    estado_minimo: EstadoMaterial
    presupuesto_maximo: Decimal | None
    dimensiones_minimas: DimensionesSchema
    estado: EstadoNecesidad
    empresa: EmpresaResumenResponse
    creado_en: datetime
    actualizado_en: datetime
