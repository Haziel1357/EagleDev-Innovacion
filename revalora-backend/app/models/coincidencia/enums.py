"""Enumeraciones del módulo coincidencia."""

from enum import StrEnum


class OrigenCoincidencia(StrEnum):
    PUBLICACION_MATERIAL = "PUBLICACION_MATERIAL"
    """Se calculó al publicar o actualizar un material sobrante."""
    PUBLICACION_NECESIDAD = "PUBLICACION_NECESIDAD"
    """Se calculó al publicar o actualizar una necesidad."""
    MANUAL = "MANUAL"
    """El usuario pidió recalcular las coincidencias."""
