"""Enumeraciones del módulo ia."""

from enum import StrEnum


class EstadoVerificacion(StrEnum):
    PENDIENTE = "PENDIENTE"
    """La IA clasificó la foto y el usuario aún no responde."""
    CONFIRMADA = "CONFIRMADA"
    """El usuario aceptó el material que propuso la IA."""
    CORREGIDA = "CORREGIDA"
    """El usuario indicó otro material distinto al propuesto."""
