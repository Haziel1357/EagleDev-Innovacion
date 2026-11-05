"""Repositorio de ProductoSugerido: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import ProductoSugerido
from app.repositories.base_repository import RepositorioBase


class ProductoSugeridoRepository(RepositorioBase[ProductoSugerido]):
    modelo = ProductoSugerido

    def de_oportunidad(self, oportunidad_id: int) -> Sequence[ProductoSugerido]:
        return self.db.scalars(
            select(ProductoSugerido)
            .where(ProductoSugerido.oportunidad_id == oportunidad_id)
            .order_by(ProductoSugerido.viabilidad.desc())
        ).all()
