"""Repositorio de MaterialSobrante: consultas y persistencia con SQLAlchemy."""

from collections.abc import Sequence
from math import cos, radians

from sqlalchemy import Select, func, or_, select

from app.exceptions import DatosInvalidosError
from app.models import (
    CategoriaMaterial,
    DisponibilidadMaterial,
    Empresa,
    EstadoMaterial,
    MaterialSobrante,
    Ubicacion,
)
from app.repositories.base_repository import RepositorioBase
from app.schemas.material_schema import FiltroMaterialRequest
from app.utils.geo_distancia import distancia_km

_KM_POR_GRADO = 111.32


class MaterialSobranteRepository(RepositorioBase[MaterialSobrante]):
    modelo = MaterialSobrante

    def _consulta_filtrada(
        self,
        filtro: FiltroMaterialRequest,
        *,
        solo_disponibles: bool,
        excluir_empresa_id: int | None,
    ) -> Select:
        consulta = (
            select(MaterialSobrante)
            .join(MaterialSobrante.empresa)
            .join(Empresa.ubicacion)
            .join(MaterialSobrante.categoria)
        )
        if solo_disponibles:
            consulta = consulta.where(
                MaterialSobrante.disponibilidad == DisponibilidadMaterial.DISPONIBLE
            )
        if excluir_empresa_id is not None:
            consulta = consulta.where(MaterialSobrante.empresa_id != excluir_empresa_id)
        if filtro.texto:
            patron = f"%{filtro.texto.strip()}%"
            consulta = consulta.where(
                or_(
                    MaterialSobrante.titulo.ilike(patron),
                    MaterialSobrante.descripcion.ilike(patron),
                )
            )
        if filtro.categoria_id is not None:
            consulta = consulta.where(MaterialSobrante.categoria_id == filtro.categoria_id)
        if filtro.categoria_codigo:
            consulta = consulta.where(CategoriaMaterial.codigo == filtro.categoria_codigo.lower())
        if filtro.estado_minimo is not None:
            aceptables = [e for e in EstadoMaterial if e.nivel >= filtro.estado_minimo.nivel]
            consulta = consulta.where(MaterialSobrante.estado.in_(aceptables))
        if filtro.tipo_oferta is not None:
            consulta = consulta.where(MaterialSobrante.tipo_oferta == filtro.tipo_oferta)
        if filtro.precio_maximo is not None:
            consulta = consulta.where(
                or_(
                    MaterialSobrante.precio.is_(None),
                    MaterialSobrante.precio <= filtro.precio_maximo,
                )
            )
        if filtro.ciudad:
            consulta = consulta.where(func.lower(Ubicacion.ciudad) == filtro.ciudad.strip().lower())
        if filtro.solo_verificados:
            consulta = consulta.where(MaterialSobrante.verificado_ia.is_(True))
        if filtro.radio_km is not None and filtro.coordenadas is not None:
            # Recorte rápido por un cuadro alrededor del punto; la distancia exacta se
            # calcula después en Python (funciona igual en PostgreSQL y en SQLite).
            lat, lon = filtro.coordenadas
            delta_lat = filtro.radio_km / _KM_POR_GRADO
            delta_lon = filtro.radio_km / (_KM_POR_GRADO * max(cos(radians(lat)), 0.01))
            consulta = consulta.where(
                Ubicacion.latitud.between(lat - delta_lat, lat + delta_lat),
                Ubicacion.longitud.between(lon - delta_lon, lon + delta_lon),
            )
        return consulta

    def buscar(
        self,
        filtro: FiltroMaterialRequest,
        *,
        offset: int,
        limite: int,
        orden: str = "recientes",
        solo_disponibles: bool = True,
        excluir_empresa_id: int | None = None,
    ) -> tuple[Sequence[MaterialSobrante], int]:
        """Busca materiales según el filtro.

        A cada material devuelto se le asigna el atributo ``distancia_km`` cuando el
        filtro trae coordenadas.
        """
        if filtro.coordenadas is None and filtro.radio_km is not None:
            raise DatosInvalidosError("Para filtrar por radio indica latitud y longitud.")
        if filtro.coordenadas is None and orden == "cercania":
            raise DatosInvalidosError("Para ordenar por cercanía indica latitud y longitud.")

        consulta = self._consulta_filtrada(
            filtro, solo_disponibles=solo_disponibles, excluir_empresa_id=excluir_empresa_id
        )
        origen = filtro.coordenadas
        necesita_distancia = origen is not None and (
            filtro.radio_km is not None or orden == "cercania"
        )

        if not necesita_distancia:
            if orden == "precio":
                consulta = consulta.order_by(
                    MaterialSobrante.precio.is_(None), MaterialSobrante.precio, MaterialSobrante.id
                )
            else:
                consulta = consulta.order_by(
                    MaterialSobrante.creado_en.desc(), MaterialSobrante.id.desc()
                )
            elementos, total = self.paginar(consulta, offset, limite)
            self._asignar_distancias(elementos, origen)
            return elementos, total

        # Filtro por radio u orden por cercanía: se resuelve en memoria sobre los candidatos.
        candidatos = list(self.db.scalars(consulta).unique().all())
        self._asignar_distancias(candidatos, origen)
        if filtro.radio_km is not None:
            candidatos = [
                m
                for m in candidatos
                if m.distancia_km is not None and m.distancia_km <= filtro.radio_km
            ]
        if orden == "precio":
            candidatos.sort(key=lambda m: (m.precio is None, m.precio or 0, m.id))
        elif orden == "cercania":
            candidatos.sort(key=lambda m: (m.distancia_km is None, m.distancia_km or 0, m.id))
        else:
            candidatos.sort(key=lambda m: (m.creado_en, m.id), reverse=True)
        return candidatos[offset : offset + limite], len(candidatos)

    @staticmethod
    def _asignar_distancias(
        materiales: Sequence[MaterialSobrante], origen: tuple[float, float] | None
    ) -> None:
        for material in materiales:
            destino = material.empresa.ubicacion.coordenadas
            material.distancia_km = (
                round(distancia_km(origen, destino), 2) if origen and destino else None
            )

    def de_empresa(
        self, empresa_id: int, offset: int, limite: int
    ) -> tuple[Sequence[MaterialSobrante], int]:
        consulta = (
            select(MaterialSobrante)
            .where(MaterialSobrante.empresa_id == empresa_id)
            .order_by(MaterialSobrante.creado_en.desc(), MaterialSobrante.id.desc())
        )
        return self.paginar(consulta, offset, limite)

    def disponibles_de_empresa(self, empresa_id: int) -> Sequence[MaterialSobrante]:
        return (
            self.db.scalars(
                select(MaterialSobrante).where(
                    MaterialSobrante.empresa_id == empresa_id,
                    MaterialSobrante.disponibilidad == DisponibilidadMaterial.DISPONIBLE,
                )
            )
            .unique()
            .all()
        )

    def disponibles_por_categoria(
        self, categoria_id: int, excluir_empresa_id: int | None = None
    ) -> Sequence[MaterialSobrante]:
        consulta = select(MaterialSobrante).where(
            MaterialSobrante.categoria_id == categoria_id,
            MaterialSobrante.disponibilidad == DisponibilidadMaterial.DISPONIBLE,
        )
        if excluir_empresa_id is not None:
            consulta = consulta.where(MaterialSobrante.empresa_id != excluir_empresa_id)
        return self.db.scalars(consulta).unique().all()

    def contar_disponibles_por_categoria(self, categoria_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(MaterialSobrante.id)).where(
                    MaterialSobrante.categoria_id == categoria_id,
                    MaterialSobrante.disponibilidad == DisponibilidadMaterial.DISPONIBLE,
                )
            )
            or 0
        )
