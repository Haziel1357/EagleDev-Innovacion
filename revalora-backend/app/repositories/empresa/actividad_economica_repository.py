"""Repositorio de ActividadEconomica: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import ActividadEconomica
from app.repositories.base_repository import RepositorioBase


class ActividadEconomicaRepository(RepositorioBase[ActividadEconomica]):
    modelo = ActividadEconomica

    def listar(self) -> Sequence[ActividadEconomica]:
        return self.db.scalars(select(ActividadEconomica).order_by(ActividadEconomica.codigo)).all()
