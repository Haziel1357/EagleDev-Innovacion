"""Dependencias de FastAPI compartidas por los endpoints.

El clasificador y el motor se crean una sola vez (en el arranque) y se guardan en
``app.state``. Las pruebas pueden sustituirlos con ``app.dependency_overrides``.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.ml.recomendacion.catalogo import obtener_catalogo
from app.ml.recomendacion.motor_recomendacion import MotorRecomendacion
from app.ml.vision.clasificador_materiales import ClasificadorMateriales, ProveedorClasificador


def obtener_proveedor(request: Request) -> ProveedorClasificador:
    return request.app.state.proveedor_clasificador


def obtener_clasificador(
    proveedor: Annotated[ProveedorClasificador, Depends(obtener_proveedor)],
) -> ClasificadorMateriales:
    return proveedor.obtener()


@lru_cache
def obtener_motor() -> MotorRecomendacion:
    return MotorRecomendacion(obtener_catalogo())


ClasificadorDep = Annotated[ClasificadorMateriales, Depends(obtener_clasificador)]
ProveedorDep = Annotated[ProveedorClasificador, Depends(obtener_proveedor)]
MotorDep = Annotated[MotorRecomendacion, Depends(obtener_motor)]
