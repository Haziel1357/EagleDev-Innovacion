"""Esquemas de POST /api/v1/oportunidades (ver docs/contrato-api-ia.md)."""

from pydantic import BaseModel, Field


class OportunidadesRequest(BaseModel):
    materiales: list[str] = Field(
        min_length=1,
        max_length=50,
        description="Códigos de los materiales disponibles.",
        examples=[["madera", "tela"]],
    )
    max_productos: int = Field(default=5, ge=1, le=20)


class MaterialFaltante(BaseModel):
    material: str = Field(examples=["vidrio"])
    descripcion: str | None = Field(default=None, examples=["protección frontal"])


class ProductoSugerido(BaseModel):
    nombre: str = Field(examples=["Marco para cuadros"])
    descripcion: str | None = None
    viabilidad: float = Field(
        ge=0, le=1, description="1 = se tienen todos los materiales.", examples=[0.6]
    )
    materiales_utilizados: list[str] = Field(examples=[["madera"]])
    materiales_faltantes: list[MaterialFaltante]


class OportunidadesResponse(BaseModel):
    productos: list[ProductoSugerido]
