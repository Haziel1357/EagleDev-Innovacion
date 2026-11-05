"""Esquemas Pydantic (entrada y salida) del módulo oportunidad."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.comun_schema import EsquemaORM
from app.schemas.material_schema import CategoriaMaterialResponse


class AnalisisOportunidadRequest(BaseModel):
    categoria_ids: list[int] | None = Field(
        default=None,
        description="Materiales a analizar. Si se omite, se usan los materiales "
        "disponibles que tiene publicados tu empresa.",
    )
    max_productos: int = Field(default=5, ge=1, le=20)


class MaterialFaltanteResponse(EsquemaORM):
    material: str
    categoria: CategoriaMaterialResponse | None
    descripcion: str | None
    disponibles_en_plataforma: int


class ProductoSugeridoResponse(EsquemaORM):
    id: int
    nombre: str
    descripcion: str | None
    viabilidad: float
    materiales_utilizados: list[str]
    materiales_faltantes: list[MaterialFaltanteResponse]


class OportunidadProductivaResponse(EsquemaORM):
    id: int
    empresa_id: int
    materiales_analizados: list[str]
    productos: list[ProductoSugeridoResponse]
    creado_en: datetime
