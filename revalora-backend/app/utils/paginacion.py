"""Utilidades de paginación para consultas y respuestas."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated, TypeVar

from fastapi import Depends, Query

from app.schemas.comun_schema import PaginaResponse

T = TypeVar("T")


@dataclass(frozen=True)
class Paginacion:
    pagina: int = 1
    tamano: int = 20

    @property
    def offset(self) -> int:
        return (self.pagina - 1) * self.tamano


def _parametros_paginacion(
    pagina: Annotated[int, Query(ge=1, description="Número de página (desde 1).")] = 1,
    tamano: Annotated[int, Query(ge=1, le=100, description="Elementos por página.")] = 20,
) -> Paginacion:
    return Paginacion(pagina=pagina, tamano=tamano)


PaginacionDep = Annotated[Paginacion, Depends(_parametros_paginacion)]


def construir_pagina(
    elementos: Sequence[T], total: int, paginacion: Paginacion
) -> PaginaResponse[T]:
    return PaginaResponse(
        elementos=list(elementos),
        total=total,
        pagina=paginacion.pagina,
        tamano=paginacion.tamano,
    )
