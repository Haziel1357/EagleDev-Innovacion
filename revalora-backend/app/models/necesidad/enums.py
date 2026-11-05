"""Enumeraciones del módulo necesidad."""

from enum import StrEnum


class EstadoNecesidad(StrEnum):
    ABIERTA = "ABIERTA"
    ATENDIDA = "ATENDIDA"
    CERRADA = "CERRADA"
