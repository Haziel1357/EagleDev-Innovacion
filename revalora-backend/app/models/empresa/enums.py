"""Enumeraciones del módulo empresa."""

from enum import StrEnum


class TipoEmpresa(StrEnum):
    MICROEMPRESA = "MICROEMPRESA"
    PEQUENA_EMPRESA = "PEQUENA_EMPRESA"
    EMPRENDIMIENTO = "EMPRENDIMIENTO"
