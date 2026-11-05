"""Esquemas Pydantic (entrada y salida) del módulo transaccion."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.models.transaccion.enums import EstadoSolicitud, TipoSolicitud
from app.schemas.comun_schema import EsquemaORM
from app.schemas.empresa_schema import EmpresaResumenResponse
from app.schemas.material_schema import MaterialSobranteResponse


class SolicitudRequest(BaseModel):
    material_id: int
    tipo: TipoSolicitud
    cantidad: Decimal = Field(gt=0, max_digits=12, decimal_places=3)
    mensaje: str | None = Field(default=None, max_length=1000)
    precio_ofrecido: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    material_ofrecido_id: int | None = Field(
        default=None, description="Obligatorio en un intercambio: material que ofreces a cambio."
    )

    @model_validator(mode="after")
    def _intercambio_requiere_material(self) -> "SolicitudRequest":
        if self.tipo == TipoSolicitud.INTERCAMBIO and self.material_ofrecido_id is None:
            raise ValueError("En un intercambio indica el material que ofreces a cambio.")
        if self.tipo != TipoSolicitud.INTERCAMBIO:
            self.material_ofrecido_id = None
        return self


class RespuestaSolicitudRequest(BaseModel):
    comentario: str | None = Field(default=None, max_length=500)


class HistorialOperacionResponse(EsquemaORM):
    id: int
    solicitud_id: int
    usuario_id: int
    estado_anterior: EstadoSolicitud | None
    estado_nuevo: EstadoSolicitud
    comentario: str | None
    creado_en: datetime


class SolicitudResponse(EsquemaORM):
    id: int
    tipo: TipoSolicitud
    estado: EstadoSolicitud
    cantidad: Decimal
    mensaje: str | None
    precio_ofrecido: Decimal | None
    material: MaterialSobranteResponse
    material_ofrecido: MaterialSobranteResponse | None
    empresa_solicitante: EmpresaResumenResponse
    historial: list[HistorialOperacionResponse]
    creado_en: datetime
    actualizado_en: datetime
