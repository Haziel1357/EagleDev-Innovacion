"""Esquemas Pydantic del módulo ia.

Incluye dos grupos:

- Esquemas de la API del backend (lo que recibe y devuelve /ia/...).
- Contrato con revalora-ia-service: el formato de las respuestas del servicio de IA
  (ver docs/contrato-api-ia.md). Solo los usa ``IaServiceClient``.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.ia.enums import EstadoVerificacion
from app.schemas.comun_schema import EsquemaORM
from app.schemas.material_schema import CategoriaMaterialResponse

# --------------------------------------------------------------------------- API backend


class ConfirmacionClasificacionRequest(BaseModel):
    categoria_id: int | None = Field(
        default=None,
        description="Categoría correcta. Si se omite, se acepta la que propuso la IA.",
    )
    material_id: int | None = Field(
        default=None, description="Material sobrante al que pertenece la foto (opcional)."
    )


class PrediccionMaterialResponse(BaseModel):
    material: str
    confianza: float
    categoria_id: int | None = None


class ReconocimientoResponse(EsquemaORM):
    id: int
    imagen_url: str
    material_predicho: str
    confianza: float
    confianza_baja: bool = Field(
        default=False, description="True si la confianza es baja y conviene revisar el resultado."
    )
    categoria_predicha: CategoriaMaterialResponse | None
    predicciones: list[PrediccionMaterialResponse]
    estado_verificacion: EstadoVerificacion
    categoria_confirmada: CategoriaMaterialResponse | None
    material_id: int | None
    creado_en: datetime


# ------------------------------------------------------ Contrato con revalora-ia-service


class PrediccionIA(BaseModel):
    material: str
    confianza: float = Field(ge=0, le=1)


class RespuestaReconocimientoIA(BaseModel):
    """POST /api/v1/reconocimiento"""

    material: str
    confianza: float = Field(ge=0, le=1)
    predicciones: list[PrediccionIA] = []


class MaterialRecomendadoIA(BaseModel):
    material: str
    funcion: str | None = None
    cantidad_estimada: Decimal | None = None
    unidad: str | None = None


class RespuestaRecomendacionIA(BaseModel):
    """POST /api/v1/recomendacion"""

    producto: str | None = None
    materiales: list[MaterialRecomendadoIA] = []


class MaterialFaltanteIA(BaseModel):
    material: str
    descripcion: str | None = None


class ProductoSugeridoIA(BaseModel):
    nombre: str
    descripcion: str | None = None
    viabilidad: float = Field(default=0.0, ge=0, le=1)
    materiales_utilizados: list[str] = []
    materiales_faltantes: list[MaterialFaltanteIA] = []


class RespuestaOportunidadesIA(BaseModel):
    """POST /api/v1/oportunidades"""

    productos: list[ProductoSugeridoIA] = []
