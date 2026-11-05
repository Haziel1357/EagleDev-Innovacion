"""Repositorio de Usuario: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import func, select

from app.models import Usuario
from app.repositories.base_repository import RepositorioBase


class UsuarioRepository(RepositorioBase[Usuario]):
    modelo = Usuario

    def por_email(self, email: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))

    def existe_email(self, email: str) -> bool:
        return self.por_email(email) is not None

    def listar_paginado(self, offset: int, limite: int) -> tuple[Sequence[Usuario], int]:
        return self.paginar(select(Usuario).order_by(Usuario.id), offset, limite)
