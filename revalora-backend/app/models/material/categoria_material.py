"""Entidad CategoriaMaterial: madera, cartón, plástico, tela, metal, etc."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class CategoriaMaterial(Base):
    __tablename__ = "categorias_material"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Código estable que se comparte con el servicio de IA (p. ej. "madera", "carton").
    codigo: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str | None] = mapped_column(String(300))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
