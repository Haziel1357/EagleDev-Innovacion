"""Repositorio de NecesidadMaterial: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import or_, select

from app.models import EstadoNecesidad, NecesidadMaterial
from app.repositories.base_repository import RepositorioBase


class NecesidadMaterialRepository(RepositorioBase[NecesidadMaterial]):
    modelo = NecesidadMaterial

    def buscar(
        self,
        *,
        texto: str | None,
        categoria_id: int | None,
        estado: EstadoNecesidad | None,
        empresa_id: int | None,
        offset: int,
        limite: int,
    ) -> tuple[Sequence[NecesidadMaterial], int]:
        consulta = select(NecesidadMaterial)
        if texto:
            patron = f"%{texto.strip()}%"
            consulta = consulta.where(
                or_(
                    NecesidadMaterial.titulo.ilike(patron),
                    NecesidadMaterial.descripcion.ilike(patron),
                )
            )
        if categoria_id is not None:
            consulta = consulta.where(NecesidadMaterial.categoria_id == categoria_id)
        if estado is not None:
            consulta = consulta.where(NecesidadMaterial.estado == estado)
        if empresa_id is not None:
            consulta = consulta.where(NecesidadMaterial.empresa_id == empresa_id)
        consulta = consulta.order_by(
            NecesidadMaterial.creado_en.desc(), NecesidadMaterial.id.desc()
        )
        return self.paginar(consulta, offset, limite)

    def abiertas_por_categoria(
        self, categoria_id: int, excluir_empresa_id: int | None = None
    ) -> Sequence[NecesidadMaterial]:
        consulta = select(NecesidadMaterial).where(
            NecesidadMaterial.categoria_id == categoria_id,
            NecesidadMaterial.estado == EstadoNecesidad.ABIERTA,
        )
        if excluir_empresa_id is not None:
            consulta = consulta.where(NecesidadMaterial.empresa_id != excluir_empresa_id)
        return self.db.scalars(consulta).unique().all()
