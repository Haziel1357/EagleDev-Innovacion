"""Entidad MaterialRequerido: material que la IA deduce como necesario para una búsqueda de fabricación."""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, columna_enum
from app.models.material.categoria_material import CategoriaMaterial
from app.models.material.enums import UnidadMedida

if TYPE_CHECKING:
    from app.models.buscador.busqueda_fabricacion import BusquedaFabricacion


class MaterialRequerido(Base):
    __tablename__ = "materiales_requeridos"

    id: Mapped[int] = mapped_column(primary_key=True)
    busqueda_id: Mapped[int] = mapped_column(
        ForeignKey("busquedas_fabricacion.id", ondelete="CASCADE"), index=True
    )
    # Código del material tal como lo devuelve la IA (p. ej. "vidrio").
    material: Mapped[str] = mapped_column(String(40))
    # Categoría de la plataforma que corresponde a ese código (si existe).
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias_material.id"))
    # Para qué sirve en el producto (p. ej. "estructura", "protección", "respaldo").
    funcion: Mapped[str | None] = mapped_column(String(100))
    cantidad_estimada: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    unidad_medida: Mapped[UnidadMedida | None] = mapped_column(columna_enum(UnidadMedida))

    busqueda: Mapped["BusquedaFabricacion"] = relationship(back_populates="materiales_requeridos")
    categoria: Mapped[CategoriaMaterial | None] = relationship(lazy="joined")
