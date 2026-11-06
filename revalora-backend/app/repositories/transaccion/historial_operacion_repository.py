"""Repositorio de HistorialOperacion: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import or_, select

from app.models import HistorialOperacion, MaterialSobrante, Solicitud
from app.repositories.base_repository import RepositorioBase


class HistorialOperacionRepository(RepositorioBase[HistorialOperacion]):
    modelo = HistorialOperacion

    def de_solicitud(self, solicitud_id: int) -> Sequence[HistorialOperacion]:
        return self.db.scalars(
            select(HistorialOperacion)
            .where(HistorialOperacion.solicitud_id == solicitud_id)
            .order_by(HistorialOperacion.id)
        ).all()

    def de_empresa(
        self, empresa_id: int, offset: int, limite: int
    ) -> tuple[Sequence[HistorialOperacion], int]:
        """Operaciones de las solicitudes en que participa la empresa (como solicitante u ofertante)."""
        materiales = select(MaterialSobrante.id).where(MaterialSobrante.empresa_id == empresa_id)
        solicitudes = select(Solicitud.id).where(
            or_(
                Solicitud.empresa_solicitante_id == empresa_id,
                Solicitud.material_id.in_(materiales),
            )
        )
        consulta = (
            select(HistorialOperacion)
            .where(HistorialOperacion.solicitud_id.in_(solicitudes))
            .order_by(HistorialOperacion.id.desc())
        )
        return self.paginar(consulta, offset, limite)
