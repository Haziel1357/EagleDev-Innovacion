"""Entidad BusquedaFabricacion: búsqueda en la que el usuario describe lo que quiere fabricar."""

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.buscador.material_requerido import MaterialRequerido


class BusquedaFabricacion(TimestampMixin, Base):
    __tablename__ = "busquedas_fabricacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    descripcion: Mapped[str] = mapped_column(String(500))
    # Nombre del producto que interpretó la IA (p. ej. "marco para cuadros").
    producto_interpretado: Mapped[str | None] = mapped_column(String(150))

    materiales_requeridos: Mapped[list[MaterialRequerido]] = relationship(
        back_populates="busqueda", cascade="all, delete-orphan", lazy="selectin"
    )
