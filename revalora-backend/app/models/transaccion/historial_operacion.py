"""Entidad HistorialOperacion: registro de los cambios de estado de una solicitud."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.transaccion.enums import EstadoSolicitud

if TYPE_CHECKING:
    from app.models.transaccion.solicitud import Solicitud


class HistorialOperacion(TimestampMixin, Base):
    __tablename__ = "historial_operaciones"

    id: Mapped[int] = mapped_column(primary_key=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes.id", ondelete="CASCADE"), index=True
    )
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    estado_anterior: Mapped[EstadoSolicitud | None] = mapped_column(columna_enum(EstadoSolicitud))
    estado_nuevo: Mapped[EstadoSolicitud] = mapped_column(columna_enum(EstadoSolicitud))
    comentario: Mapped[str | None] = mapped_column(String(500))

    solicitud: Mapped["Solicitud"] = relationship(back_populates="historial")
