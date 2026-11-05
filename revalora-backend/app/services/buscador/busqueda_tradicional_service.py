"""Búsqueda tradicional de materiales por filtros."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models import MaterialSobrante, Usuario
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.schemas.buscador_schema import BusquedaTradicionalRequest


class BusquedaTradicionalService:
    def __init__(self, db: Session) -> None:
        self.materiales = MaterialSobranteRepository(db)

    def buscar(
        self,
        filtro: BusquedaTradicionalRequest,
        usuario: Usuario | None,
        offset: int,
        limite: int,
    ) -> tuple[Sequence[MaterialSobrante], int]:
        """Busca materiales disponibles. Sin coordenadas, usa la ubicación de la empresa del usuario."""
        if filtro.coordenadas is None and usuario is not None and usuario.empresa is not None:
            coordenadas = usuario.empresa.ubicacion.coordenadas
            if coordenadas is not None:
                filtro = filtro.model_copy(
                    update={"latitud": coordenadas[0], "longitud": coordenadas[1]}
                )

        return self.materiales.buscar(
            filtro,
            offset=offset,
            limite=limite,
            orden=filtro.orden,
            excluir_empresa_id=usuario.empresa_id if usuario else None,
        )
