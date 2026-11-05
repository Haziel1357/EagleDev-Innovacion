"""Repositorio base con las operaciones comunes de persistencia."""

from collections.abc import Sequence
from typing import Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.base import Base

M = TypeVar("M", bound=Base)


class RepositorioBase(Generic[M]):
    modelo: type[M]

    def __init__(self, db: Session) -> None:
        self.db = db

    def obtener(self, id_: int) -> M | None:
        return self.db.get(self.modelo, id_)

    def listar(self) -> Sequence[M]:
        return self.db.scalars(select(self.modelo).order_by(self.modelo.id)).all()

    def agregar(self, entidad: M) -> M:
        self.db.add(entidad)
        self.db.flush()
        return entidad

    def eliminar(self, entidad: M) -> None:
        self.db.delete(entidad)
        self.db.flush()

    def paginar(self, consulta: Select, offset: int, limite: int) -> tuple[Sequence[M], int]:
        """Ejecuta la consulta con límite y devuelve (elementos, total sin paginar)."""
        total = self.db.scalar(select(func.count()).select_from(consulta.order_by(None).subquery()))
        elementos = self.db.scalars(consulta.offset(offset).limit(limite)).unique().all()
        return elementos, total or 0
