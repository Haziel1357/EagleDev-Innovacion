"""Repositorio de OportunidadProductiva: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import OportunidadProductiva
from app.repositories.base_repository import RepositorioBase


class OportunidadProductivaRepository(RepositorioBase[OportunidadProductiva]):
    modelo = OportunidadProductiva

    def de_empresa(
        self, empresa_id: int, offset: int, limite: int
    ) -> tuple[Sequence[OportunidadProductiva], int]:
        consulta = (
            select(OportunidadProductiva)
            .where(OportunidadProductiva.empresa_id == empresa_id)
            .order_by(OportunidadProductiva.id.desc())
        )
        return self.paginar(consulta, offset, limite)
