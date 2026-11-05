"""Registro y consulta del historial de operaciones."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.models import Empresa, EstadoSolicitud, HistorialOperacion, Solicitud, Usuario
from app.repositories.transaccion.historial_operacion_repository import HistorialOperacionRepository


class HistorialOperacionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.historial = HistorialOperacionRepository(db)

    def registrar(
        self,
        solicitud: Solicitud,
        usuario: Usuario,
        estado_anterior: EstadoSolicitud | None,
        estado_nuevo: EstadoSolicitud,
        comentario: str | None = None,
    ) -> HistorialOperacion:
        """Añade una entrada al historial (sin confirmar la transacción)."""
        entrada = HistorialOperacion(
            usuario_id=usuario.id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            comentario=comentario,
        )
        solicitud.historial.append(entrada)
        return entrada

    def de_empresa(
        self, empresa: Empresa, offset: int, limite: int
    ) -> tuple[Sequence[HistorialOperacion], int]:
        return self.historial.de_empresa(empresa.id, offset, limite)
