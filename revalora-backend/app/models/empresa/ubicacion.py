"""Ubicacion: dirección y coordenadas de una empresa."""

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Ubicacion(Base):
    __tablename__ = "ubicaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    direccion: Mapped[str | None] = mapped_column(String(255))
    ciudad: Mapped[str] = mapped_column(String(100), index=True)
    region: Mapped[str | None] = mapped_column(String(100))
    pais: Mapped[str] = mapped_column(String(100), default="Colombia")
    latitud: Mapped[float | None] = mapped_column(Float)
    longitud: Mapped[float | None] = mapped_column(Float)

    @property
    def coordenadas(self) -> tuple[float, float] | None:
        if self.latitud is None or self.longitud is None:
            return None
        return (self.latitud, self.longitud)
