"""Entidad ProductoSugerido: producto que se puede fabricar dentro de una oportunidad productiva."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.oportunidad.material_faltante import MaterialFaltante

if TYPE_CHECKING:
    from app.models.oportunidad.oportunidad_productiva import OportunidadProductiva


class ProductoSugerido(Base):
    __tablename__ = "productos_sugeridos"

    id: Mapped[int] = mapped_column(primary_key=True)
    oportunidad_id: Mapped[int] = mapped_column(
        ForeignKey("oportunidades_productivas.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)
    # Qué tan factible es fabricarlo con lo disponible (0-1).
    viabilidad: Mapped[float] = mapped_column(Float, default=0.0)
    materiales_utilizados: Mapped[list[Any]] = mapped_column(JSON, default=list)

    oportunidad: Mapped["OportunidadProductiva"] = relationship(back_populates="productos")
    materiales_faltantes: Mapped[list[MaterialFaltante]] = relationship(
        back_populates="producto", cascade="all, delete-orphan", lazy="selectin"
    )
