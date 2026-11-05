"""Repositorio de CategoriaMaterial: consultas y persistencia con SQLAlchemy."""

from collections.abc import Iterable, Sequence

from sqlalchemy import select

from app.models import CategoriaMaterial
from app.repositories.base_repository import RepositorioBase


class CategoriaMaterialRepository(RepositorioBase[CategoriaMaterial]):
    modelo = CategoriaMaterial

    def listar(self, solo_activas: bool = False) -> Sequence[CategoriaMaterial]:
        consulta = select(CategoriaMaterial).order_by(CategoriaMaterial.nombre)
        if solo_activas:
            consulta = consulta.where(CategoriaMaterial.activa.is_(True))
        return self.db.scalars(consulta).all()

    def por_codigo(self, codigo: str) -> CategoriaMaterial | None:
        return self.db.scalar(
            select(CategoriaMaterial).where(CategoriaMaterial.codigo == codigo.strip().lower())
        )

    def por_codigos(self, codigos: Iterable[str]) -> dict[str, CategoriaMaterial]:
        normalizados = {c.strip().lower() for c in codigos}
        if not normalizados:
            return {}
        categorias = self.db.scalars(
            select(CategoriaMaterial).where(CategoriaMaterial.codigo.in_(normalizados))
        ).all()
        return {c.codigo: c for c in categorias}

    def por_ids(self, ids: Iterable[int]) -> Sequence[CategoriaMaterial]:
        return self.db.scalars(
            select(CategoriaMaterial).where(CategoriaMaterial.id.in_(set(ids)))
        ).all()
