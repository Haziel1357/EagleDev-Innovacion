"""Lógica de negocio de categorías de materiales."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontradoError, ReglaNegocioError
from app.models import CategoriaMaterial
from app.repositories.material.categoria_material_repository import CategoriaMaterialRepository
from app.schemas.material_schema import CategoriaMaterialRequest


class CategoriaMaterialService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.categorias = CategoriaMaterialRepository(db)

    def listar(self, solo_activas: bool = True) -> Sequence[CategoriaMaterial]:
        return self.categorias.listar(solo_activas=solo_activas)

    def obtener(self, categoria_id: int) -> CategoriaMaterial:
        categoria = self.categorias.obtener(categoria_id)
        if categoria is None:
            raise RecursoNoEncontradoError("Categoría de material no encontrada.")
        return categoria

    def obtener_activa(self, categoria_id: int) -> CategoriaMaterial:
        categoria = self.obtener(categoria_id)
        if not categoria.activa:
            raise ReglaNegocioError("La categoría de material no está activa.")
        return categoria

    def crear(self, datos: CategoriaMaterialRequest) -> CategoriaMaterial:
        if self.categorias.por_codigo(datos.codigo) is not None:
            raise ReglaNegocioError("Ya existe una categoría con ese código.")
        categoria = self.categorias.agregar(CategoriaMaterial(**datos.model_dump()))
        self.db.commit()
        return categoria

    def actualizar(self, categoria_id: int, datos: CategoriaMaterialRequest) -> CategoriaMaterial:
        categoria = self.obtener(categoria_id)
        existente = self.categorias.por_codigo(datos.codigo)
        if existente is not None and existente.id != categoria.id:
            raise ReglaNegocioError("Ya existe una categoría con ese código.")
        for campo, valor in datos.model_dump().items():
            setattr(categoria, campo, valor)
        self.db.commit()
        return categoria
