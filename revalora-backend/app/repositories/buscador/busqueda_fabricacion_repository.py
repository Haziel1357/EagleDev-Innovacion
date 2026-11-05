"""Repositorio de BusquedaFabricacion: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import BusquedaFabricacion
from app.repositories.base_repository import RepositorioBase


class BusquedaFabricacionRepository(RepositorioBase[BusquedaFabricacion]):
    modelo = BusquedaFabricacion

    def de_usuario(
        self, usuario_id: int, offset: int, limite: int
    ) -> tuple[Sequence[BusquedaFabricacion], int]:
        consulta = (
            select(BusquedaFabricacion)
            .where(BusquedaFabricacion.usuario_id == usuario_id)
            .order_by(BusquedaFabricacion.id.desc())
        )
        return self.paginar(consulta, offset, limite)
