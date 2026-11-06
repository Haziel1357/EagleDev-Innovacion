"""Entidad Coincidencia: cruce entre un material sobrante y una necesidad, con su puntuación de compatibilidad."""

from typing import Any

from sqlalchemy import JSON, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.coincidencia.enums import OrigenCoincidencia
from app.models.material.material_sobrante import MaterialSobrante
from app.models.necesidad.necesidad_material import NecesidadMaterial


class Coincidencia(TimestampMixin, Base):
    __tablename__ = "coincidencias"
    __table_args__ = (UniqueConstraint("material_id", "necesidad_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materiales_sobrantes.id", ondelete="CASCADE"), index=True
    )
    necesidad_id: Mapped[int] = mapped_column(
        ForeignKey("necesidades_material.id", ondelete="CASCADE"), index=True
    )
    # Puntuación total de 0 a 100.
    puntuacion: Mapped[float] = mapped_column(Float, index=True)
    # Puntuación de cada criterio (material, cantidad, estado, dimensiones, ubicacion, precio).
    detalle: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    distancia_km: Mapped[float | None] = mapped_column(Float)
    origen: Mapped[OrigenCoincidencia] = mapped_column(columna_enum(OrigenCoincidencia))

    material: Mapped[MaterialSobrante] = relationship(lazy="joined")
    necesidad: Mapped[NecesidadMaterial] = relationship(lazy="joined")
