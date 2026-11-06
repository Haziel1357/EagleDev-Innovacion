"""Esquemas de POST /api/v1/recomendacion (ver docs/contrato-api-ia.md)."""

from typing import Literal

from pydantic import BaseModel, Field

Unidad = Literal["UNIDAD", "KILOGRAMO", "METRO", "METRO_CUADRADO", "METRO_CUBICO", "LITRO"]


class RecomendacionRequest(BaseModel):
    descripcion: str = Field(
        min_length=3,
        max_length=1000,
        description="Producto que se quiere fabricar, en lenguaje natural.",
        examples=["Quiero fabricar marcos para cuadros"],
    )


class MaterialRecomendado(BaseModel):
    material: str = Field(examples=["madera"])
    funcion: str | None = Field(default=None, examples=["estructura del marco"])
    cantidad_estimada: float | None = Field(
        default=None, gt=0, description="Por cada unidad de producto.", examples=[2]
    )
    unidad: Unidad | None = Field(default=None, examples=["METRO"])


class RecomendacionResponse(BaseModel):
    producto: str | None = Field(
        description="Producto interpretado; null si no se reconoció ninguno del catálogo.",
        examples=["Marco para cuadros"],
    )
    materiales: list[MaterialRecomendado]
