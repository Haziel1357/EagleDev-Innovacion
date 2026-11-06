"""Esquemas de POST /api/v1/reconocimiento (ver docs/contrato-api-ia.md)."""

from pydantic import BaseModel, Field


class PrediccionMaterial(BaseModel):
    material: str = Field(examples=["madera"])
    confianza: float = Field(ge=0, le=1, examples=[0.93])


class ReconocimientoResponse(BaseModel):
    material: str = Field(description="Material con mayor confianza.", examples=["madera"])
    confianza: float = Field(ge=0, le=1, examples=[0.93])
    predicciones: list[PrediccionMaterial] = Field(
        description="Alternativas ordenadas de mayor a menor confianza (incluye la principal)."
    )
    modelo: str = Field(
        description="Clasificador que respondió: 'clip' o 'heuristico'. El backend no lo usa.",
        examples=["clip"],
    )
