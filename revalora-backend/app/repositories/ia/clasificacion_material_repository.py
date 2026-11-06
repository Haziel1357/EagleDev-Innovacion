"""Repositorio de ClasificacionMaterial: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import select

from app.models import ClasificacionMaterial
from app.repositories.base_repository import RepositorioBase


class ClasificacionMaterialRepository(RepositorioBase[ClasificacionMaterial]):
    modelo = ClasificacionMaterial

    def de_usuario(
        self, usuario_id: int, offset: int, limite: int
    ) -> tuple[Sequence[ClasificacionMaterial], int]:
        consulta = (
            select(ClasificacionMaterial)
            .where(ClasificacionMaterial.usuario_id == usuario_id)
            .order_by(ClasificacionMaterial.id.desc())
        )
        return self.paginar(consulta, offset, limite)
