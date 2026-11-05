"""Enumeraciones del módulo transaccion."""

from enum import StrEnum

from app.models.material.enums import TipoOferta


class TipoSolicitud(StrEnum):
    COMPRA = "COMPRA"
    INTERCAMBIO = "INTERCAMBIO"
    APROVECHAMIENTO = "APROVECHAMIENTO"

    @property
    def tipo_oferta(self) -> TipoOferta:
        """Tipo de oferta del material con el que es compatible esta solicitud."""
        return _OFERTA_POR_SOLICITUD[self]


_OFERTA_POR_SOLICITUD = {
    TipoSolicitud.COMPRA: TipoOferta.VENTA,
    TipoSolicitud.INTERCAMBIO: TipoOferta.INTERCAMBIO,
    TipoSolicitud.APROVECHAMIENTO: TipoOferta.APROVECHAMIENTO,
}


class EstadoSolicitud(StrEnum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"
    CANCELADA = "CANCELADA"
    COMPLETADA = "COMPLETADA"
