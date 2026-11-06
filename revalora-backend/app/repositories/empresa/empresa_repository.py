"""Repositorio de Empresa: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence

from sqlalchemy import func, select

from app.models import Empresa, TipoEmpresa, Ubicacion
from app.repositories.base_repository import RepositorioBase


class EmpresaRepository(RepositorioBase[Empresa]):
    modelo = Empresa

    def por_identificacion(self, identificacion: str) -> Empresa | None:
        return self.db.scalar(select(Empresa).where(Empresa.identificacion == identificacion))

    def buscar(
        self,
        *,
        texto: str | None,
        tipo: TipoEmpresa | None,
        ciudad: str | None,
        actividad_economica_id: int | None,
        offset: int,
        limite: int,
    ) -> tuple[Sequence[Empresa], int]:
        consulta = select(Empresa).join(Empresa.ubicacion)
        if texto:
            consulta = consulta.where(Empresa.nombre.ilike(f"%{texto}%"))
        if tipo:
            consulta = consulta.where(Empresa.tipo == tipo)
        if ciudad:
            consulta = consulta.where(func.lower(Ubicacion.ciudad) == ciudad.lower())
        if actividad_economica_id:
            consulta = consulta.where(Empresa.actividad_economica_id == actividad_economica_id)
        return self.paginar(consulta.order_by(Empresa.nombre), offset, limite)
