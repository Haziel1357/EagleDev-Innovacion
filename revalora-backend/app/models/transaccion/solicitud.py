"""Entidad Solicitud: solicitud de compra o intercambio de un material."""

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.empresa.empresa import Empresa
from app.models.material.material_sobrante import MaterialSobrante
from app.models.transaccion.enums import EstadoSolicitud, TipoSolicitud
from app.models.transaccion.historial_operacion import HistorialOperacion


class Solicitud(TimestampMixin, Base):
    __tablename__ = "solicitudes"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materiales_sobrantes.id"), index=True)
    empresa_solicitante_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    tipo: Mapped[TipoSolicitud] = mapped_column(columna_enum(TipoSolicitud))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    mensaje: Mapped[str | None] = mapped_column(Text)
    precio_ofrecido: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    # En un intercambio, material que la empresa solicitante ofrece a cambio.
    material_ofrecido_id: Mapped[int | None] = mapped_column(ForeignKey("materiales_sobrantes.id"))
    estado: Mapped[EstadoSolicitud] = mapped_column(
        columna_enum(EstadoSolicitud), default=EstadoSolicitud.PENDIENTE, index=True
    )

    material: Mapped[MaterialSobrante] = relationship(foreign_keys=[material_id], lazy="joined")
    material_ofrecido: Mapped[MaterialSobrante | None] = relationship(
        foreign_keys=[material_ofrecido_id], lazy="joined"
    )
    empresa_solicitante: Mapped[Empresa] = relationship(lazy="joined")
    historial: Mapped[list[HistorialOperacion]] = relationship(
        back_populates="solicitud",
        cascade="all, delete-orphan",
        order_by=HistorialOperacion.id,
        lazy="selectin",
    )

    @property
    def empresa_ofertante_id(self) -> int:
        return self.material.empresa_id

    def participa(self, empresa_id: int) -> bool:
        return empresa_id in (self.empresa_solicitante_id, self.empresa_ofertante_id)
