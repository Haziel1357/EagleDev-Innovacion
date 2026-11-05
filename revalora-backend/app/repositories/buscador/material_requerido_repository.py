"""Repositorio de MaterialRequerido: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import MaterialRequerido
from app.repositories.base_repository import RepositorioBase


class MaterialRequeridoRepository(RepositorioBase[MaterialRequerido]):
    modelo = MaterialRequerido

    def de_busqueda(self, busqueda_id: int) -> Sequence[MaterialRequerido]:
        return self.db.scalars(
            select(MaterialRequerido)
            .where(MaterialRequerido.busqueda_id == busqueda_id)
            .order_by(MaterialRequerido.id)
        ).all()
