"""Entidad ClasificacionMaterial: resultado del reconocimiento con IA y su verificación por el usuario."""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.ia.enums import EstadoVerificacion
from app.models.material.categoria_material import CategoriaMaterial


class ClasificacionMaterial(TimestampMixin, Base):
    __tablename__ = "clasificaciones_material"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    material_id: Mapped[int | None] = mapped_column(
        ForeignKey("materiales_sobrantes.id", ondelete="SET NULL"), index=True
    )
    # Ruta relativa de la imagen analizada dentro de la carpeta de uploads.
    ruta_imagen: Mapped[str] = mapped_column(String(255))
    tipo_mime: Mapped[str] = mapped_column(String(50))
    tamano_bytes: Mapped[int]

    # Lo que respondió la IA.
    material_predicho: Mapped[str] = mapped_column(String(40))
    confianza: Mapped[float] = mapped_column(Float)
    predicciones: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    categoria_predicha_id: Mapped[int | None] = mapped_column(ForeignKey("categorias_material.id"))

    # Lo que confirmó o corrigió el usuario.
    estado_verificacion: Mapped[EstadoVerificacion] = mapped_column(
        columna_enum(EstadoVerificacion), default=EstadoVerificacion.PENDIENTE
    )
    categoria_confirmada_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias_material.id")
    )

    categoria_predicha: Mapped[CategoriaMaterial | None] = relationship(
        foreign_keys=[categoria_predicha_id], lazy="joined"
    )
    categoria_confirmada: Mapped[CategoriaMaterial | None] = relationship(
        foreign_keys=[categoria_confirmada_id], lazy="joined"
    )

    @property
    def imagen_url(self) -> str:
        return f"/uploads/{self.ruta_imagen}"

    @property
    def confianza_baja(self) -> bool:
        from app.utils.constantes import CONFIANZA_MINIMA_IA

        return self.confianza < CONFIANZA_MINIMA_IA

    @property
    def verificada(self) -> bool:
        return self.estado_verificacion != EstadoVerificacion.PENDIENTE
