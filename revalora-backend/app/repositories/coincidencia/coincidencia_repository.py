"""Repositorio de Coincidencia: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import delete, select

from app.models import Coincidencia, MaterialSobrante, NecesidadMaterial
from app.repositories.base_repository import RepositorioBase


class CoincidenciaRepository(RepositorioBase[Coincidencia]):
    modelo = Coincidencia

    def por_par(self, material_id: int, necesidad_id: int) -> Coincidencia | None:
        return self.db.scalar(
            select(Coincidencia).where(
                Coincidencia.material_id == material_id,
                Coincidencia.necesidad_id == necesidad_id,
            )
        )

    def de_necesidad(
        self, necesidad_id: int, offset: int, limite: int
    ) -> tuple[Sequence[Coincidencia], int]:
        consulta = (
            select(Coincidencia)
            .where(Coincidencia.necesidad_id == necesidad_id)
            .order_by(Coincidencia.puntuacion.desc(), Coincidencia.id)
        )
        return self.paginar(consulta, offset, limite)

    def de_material(
        self, material_id: int, offset: int, limite: int
    ) -> tuple[Sequence[Coincidencia], int]:
        consulta = (
            select(Coincidencia)
            .where(Coincidencia.material_id == material_id)
            .order_by(Coincidencia.puntuacion.desc(), Coincidencia.id)
        )
        return self.paginar(consulta, offset, limite)

    def de_empresa(
        self, empresa_id: int, offset: int, limite: int
    ) -> tuple[Sequence[Coincidencia], int]:
        """Coincidencias en las que la empresa ofrece el material o publicó la necesidad."""
        materiales = select(MaterialSobrante.id).where(MaterialSobrante.empresa_id == empresa_id)
        necesidades = select(NecesidadMaterial.id).where(NecesidadMaterial.empresa_id == empresa_id)
        consulta = (
            select(Coincidencia)
            .where(
                Coincidencia.material_id.in_(materiales)
                | Coincidencia.necesidad_id.in_(necesidades)
            )
            .order_by(Coincidencia.puntuacion.desc(), Coincidencia.id)
        )
        return self.paginar(consulta, offset, limite)

    def eliminar_de_material(self, material_id: int, excepto: set[int]) -> None:
        """Borra las coincidencias del material cuyas necesidades ya no son compatibles."""
        consulta = delete(Coincidencia).where(Coincidencia.material_id == material_id)
        if excepto:
            consulta = consulta.where(Coincidencia.necesidad_id.not_in(excepto))
        self.db.execute(consulta)

    def eliminar_de_necesidad(self, necesidad_id: int, excepto: set[int]) -> None:
        """Borra las coincidencias de la necesidad cuyos materiales ya no son compatibles."""
        consulta = delete(Coincidencia).where(Coincidencia.necesidad_id == necesidad_id)
        if excepto:
            consulta = consulta.where(Coincidencia.material_id.not_in(excepto))
        self.db.execute(consulta)
