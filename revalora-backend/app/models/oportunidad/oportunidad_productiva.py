"""Entidad OportunidadProductiva: análisis de lo que se puede fabricar con los materiales disponibles."""

from typing import Any

from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.oportunidad.producto_sugerido import ProductoSugerido


class OportunidadProductiva(TimestampMixin, Base):
    __tablename__ = "oportunidades_productivas"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    # Códigos de los materiales que se analizaron (p. ej. ["madera", "tela"]).
    materiales_analizados: Mapped[list[Any]] = mapped_column(JSON, default=list)

    productos: Mapped[list[ProductoSugerido]] = relationship(
        back_populates="oportunidad",
        cascade="all, delete-orphan",
        order_by=ProductoSugerido.viabilidad.desc(),
        lazy="selectin",
    )
