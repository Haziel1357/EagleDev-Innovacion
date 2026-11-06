"""Esquemas Pydantic (entrada y salida) del módulo coincidencia."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.coincidencia.enums import OrigenCoincidencia
from app.schemas.comun_schema import EsquemaORM
from app.schemas.material_schema import MaterialSobranteResponse
from app.schemas.necesidad_schema import NecesidadMaterialResponse


class PuntuacionCompatibilidadResponse(BaseModel):
    """Puntuación de cada criterio (0-1) y total ponderado (0-100)."""

    total: float = Field(ge=0, le=100)
    material: float
    cantidad: float
    estado: float
    dimensiones: float
    ubicacion: float
    precio: float
    distancia_km: float | None = None


class CoincidenciaResponse(EsquemaORM):
    id: int
    puntuacion: float
    detalle: dict[str, float]
    distancia_km: float | None
    origen: OrigenCoincidencia
    material: MaterialSobranteResponse
    necesidad: NecesidadMaterialResponse
    creado_en: datetime
    actualizado_en: datetime
