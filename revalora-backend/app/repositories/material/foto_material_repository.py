"""Repositorio de FotoMaterial: consultas y persistencia con SQLAlchemy."""

from sqlalchemy import func, select

from app.models import FotoMaterial
from app.repositories.base_repository import RepositorioBase


class FotoMaterialRepository(RepositorioBase[FotoMaterial]):
    modelo = FotoMaterial

    def de_material(self, material_id: int, foto_id: int) -> FotoMaterial | None:
        return self.db.scalar(
            select(FotoMaterial).where(
                FotoMaterial.id == foto_id, FotoMaterial.material_id == material_id
            )
        )

    def contar_de_material(self, material_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(FotoMaterial.id)).where(FotoMaterial.material_id == material_id)
            )
            or 0
        )
