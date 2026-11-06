"""Entidad MaterialFaltante: material que falta para fabricar un producto sugerido."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.material.categoria_material import CategoriaMaterial

if TYPE_CHECKING:
    from app.models.oportunidad.producto_sugerido import ProductoSugerido


class MaterialFaltante(Base):
    __tablename__ = "materiales_faltantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos_sugeridos.id", ondelete="CASCADE"), index=True
    )
    material: Mapped[str] = mapped_column(String(40))
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias_material.id"))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    # Publicaciones disponibles en la plataforma con ese material al momento del análisis.
    disponibles_en_plataforma: Mapped[int] = mapped_column(Integer, default=0)

    producto: Mapped["ProductoSugerido"] = relationship(back_populates="materiales_faltantes")
    categoria: Mapped[CategoriaMaterial | None] = relationship(lazy="joined")
