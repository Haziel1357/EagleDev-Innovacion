"""Enumeraciones del módulo material."""

from enum import StrEnum


class EstadoMaterial(StrEnum):
    """Estado físico del material, de mejor a peor."""

    NUEVO = "NUEVO"
    BUENO = "BUENO"
    REGULAR = "REGULAR"
    DETERIORADO = "DETERIORADO"

    @property
    def nivel(self) -> int:
        """4 = nuevo … 1 = deteriorado. Sirve para comparar con el estado mínimo aceptable."""
        return _NIVELES_ESTADO[self]


_NIVELES_ESTADO = {
    EstadoMaterial.NUEVO: 4,
    EstadoMaterial.BUENO: 3,
    EstadoMaterial.REGULAR: 2,
    EstadoMaterial.DETERIORADO: 1,
}


class DisponibilidadMaterial(StrEnum):
    DISPONIBLE = "DISPONIBLE"
    RESERVADO = "RESERVADO"
    AGOTADO = "AGOTADO"
    RETIRADO = "RETIRADO"


class TipoOferta(StrEnum):
    VENTA = "VENTA"
    INTERCAMBIO = "INTERCAMBIO"
    APROVECHAMIENTO = "APROVECHAMIENTO"


class UnidadMedida(StrEnum):
    UNIDAD = "UNIDAD"
    KILOGRAMO = "KILOGRAMO"
    METRO = "METRO"
    METRO_CUADRADO = "METRO_CUADRADO"
    METRO_CUBICO = "METRO_CUBICO"
    LITRO = "LITRO"
