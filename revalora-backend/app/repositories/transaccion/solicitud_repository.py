"""Repositorio de Solicitud: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import EstadoSolicitud, MaterialSobrante, Solicitud
from app.repositories.base_repository import RepositorioBase


class SolicitudRepository(RepositorioBase[Solicitud]):
    modelo = Solicitud

    def enviadas(
        self, empresa_id: int, estado: EstadoSolicitud | None, offset: int, limite: int
    ) -> tuple[Sequence[Solicitud], int]:
        consulta = select(Solicitud).where(Solicitud.empresa_solicitante_id == empresa_id)
        if estado is not None:
            consulta = consulta.where(Solicitud.estado == estado)
        return self.paginar(consulta.order_by(Solicitud.id.desc()), offset, limite)

    def recibidas(
        self, empresa_id: int, estado: EstadoSolicitud | None, offset: int, limite: int
    ) -> tuple[Sequence[Solicitud], int]:
        materiales = select(MaterialSobrante.id).where(MaterialSobrante.empresa_id == empresa_id)
        consulta = select(Solicitud).where(Solicitud.material_id.in_(materiales))
        if estado is not None:
            consulta = consulta.where(Solicitud.estado == estado)
        return self.paginar(consulta.order_by(Solicitud.id.desc()), offset, limite)

    def pendientes_de_material(
        self, material_id: int, excluir_id: int | None = None
    ) -> Sequence[Solicitud]:
        consulta = select(Solicitud).where(
            Solicitud.material_id == material_id,
            Solicitud.estado == EstadoSolicitud.PENDIENTE,
        )
        if excluir_id is not None:
            consulta = consulta.where(Solicitud.id != excluir_id)
        return self.db.scalars(consulta).unique().all()

    def existe_pendiente(self, material_id: int, empresa_id: int) -> bool:
        return (
            self.db.scalar(
                select(Solicitud.id).where(
                    Solicitud.material_id == material_id,
                    Solicitud.empresa_solicitante_id == empresa_id,
                    Solicitud.estado == EstadoSolicitud.PENDIENTE,
                )
            )
            is not None
        )
