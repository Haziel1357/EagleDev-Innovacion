"""Repositorio de Rol: consultas y persistencia con SQLAlchemy."""

from sqlalchemy import select

from app.models import Rol
from app.repositories.base_repository import RepositorioBase


class RolRepository(RepositorioBase[Rol]):
    modelo = Rol

    def por_nombre(self, nombre: str) -> Rol | None:
        return self.db.scalar(select(Rol).where(Rol.nombre == nombre))
