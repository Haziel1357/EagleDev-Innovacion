"""Entidad Empresa: datos de la microempresa, pequeña empresa o emprendimiento."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.empresa.actividad_economica import ActividadEconomica
from app.models.empresa.enums import TipoEmpresa
from app.models.empresa.ubicacion import Ubicacion

if TYPE_CHECKING:
    from app.models.usuario.usuario import Usuario


class Empresa(TimestampMixin, Base):
    __tablename__ = "empresas"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), unique=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    identificacion: Mapped[str | None] = mapped_column(String(30), unique=True)
    tipo: Mapped[TipoEmpresa] = mapped_column(columna_enum(TipoEmpresa))
    descripcion: Mapped[str | None] = mapped_column(Text)
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    actividad_economica_id: Mapped[int | None] = mapped_column(
        ForeignKey("actividades_economicas.id")
    )
    ubicacion_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id"))

    usuario: Mapped["Usuario"] = relationship(back_populates="empresa")
    actividad_economica: Mapped[ActividadEconomica | None] = relationship(lazy="joined")
    ubicacion: Mapped[Ubicacion] = relationship(
        lazy="joined", cascade="all, delete-orphan", single_parent=True
    )
