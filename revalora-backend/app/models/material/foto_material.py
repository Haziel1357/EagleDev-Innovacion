"""Entidad FotoMaterial: fotografía asociada a un material sobrante."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.material.material_sobrante import MaterialSobrante


class FotoMaterial(TimestampMixin, Base):
    __tablename__ = "fotos_material"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materiales_sobrantes.id", ondelete="CASCADE"), index=True
    )
    # Ruta relativa dentro de la carpeta de uploads (p. ej. "materiales/ab12.jpg").
    ruta: Mapped[str] = mapped_column(String(255))
    nombre_original: Mapped[str | None] = mapped_column(String(255))
    tipo_mime: Mapped[str] = mapped_column(String(50))
    tamano_bytes: Mapped[int] = mapped_column(Integer)
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)

    material: Mapped["MaterialSobrante"] = relationship(back_populates="fotos")

    @property
    def url(self) -> str:
        return f"/uploads/{self.ruta}"
