"""Esquemas Pydantic (entrada y salida) del módulo buscador."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from app.models.material.enums import UnidadMedida
from app.schemas.comun_schema import EsquemaORM
from app.schemas.material_schema import (
    CategoriaMaterialResponse,
    FiltroMaterialRequest,
    MaterialSobranteResponse,
)


class BusquedaTradicionalRequest(FiltroMaterialRequest):
    orden: Literal["recientes", "precio", "cercania"] = Field(
        default="recientes",
        description="'cercania' requiere latitud y longitud.",
    )


class BusquedaFabricacionRequest(BaseModel):
    descripcion: str = Field(
        min_length=5,
        max_length=500,
        examples=["Quiero fabricar marcos para cuadros"],
    )
    latitud: float | None = Field(default=None, ge=-90, le=90)
    longitud: float | None = Field(default=None, ge=-180, le=180)
    limite_por_material: int = Field(default=10, ge=1, le=50)


class MaterialRecomendadoResponse(BaseModel):
    puntuacion: float = Field(description="Ajuste del material a la búsqueda (0-100).")
    material: MaterialSobranteResponse


class MaterialRequeridoResponse(EsquemaORM):
    material: str
    funcion: str | None
    categoria: CategoriaMaterialResponse | None
    cantidad_estimada: Decimal | None
    unidad_medida: UnidadMedida | None
    resultados: list[MaterialRecomendadoResponse] = []


class ResultadoBusquedaResponse(BaseModel):
    busqueda_id: int
    descripcion: str
    producto_interpretado: str | None
    materiales_requeridos: list[MaterialRequeridoResponse]
    total_resultados: int
    creado_en: datetime


class BusquedaHistorialResponse(EsquemaORM):
    id: int
    descripcion: str
    producto_interpretado: str | None
    materiales_requeridos: list[MaterialRequeridoResponse]
    creado_en: datetime
