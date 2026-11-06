"""Carga y validación del catálogo de productos (catalogo_productos.json)."""

import json
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from app.ml.materiales import CODIGOS_MATERIAL, UNIDADES
from app.utils.texto_utils import clave

RUTA_CATALOGO = Path(__file__).with_name("catalogo_productos.json")


class MaterialProducto(BaseModel):
    material: str
    funcion: str
    principal: bool = False
    cantidad_estimada: float | None = Field(default=None, gt=0)
    unidad: str | None = None

    @field_validator("material")
    @classmethod
    def _material_valido(cls, valor: str) -> str:
        if valor not in CODIGOS_MATERIAL:
            raise ValueError(f"material desconocido: {valor!r}")
        return valor

    @field_validator("unidad")
    @classmethod
    def _unidad_valida(cls, valor: str | None) -> str | None:
        if valor is not None and valor not in UNIDADES:
            raise ValueError(f"unidad desconocida: {valor!r}")
        return valor


class ProductoCatalogo(BaseModel):
    nombre: str = Field(min_length=3)
    descripcion: str
    palabras_clave: list[str] = Field(min_length=1)
    materiales: list[MaterialProducto] = Field(min_length=1)

    @property
    def claves(self) -> list[frozenset[str]]:
        """Palabras clave normalizadas, incluido el propio nombre del producto."""
        return [clave(k) for k in [self.nombre, *self.palabras_clave] if clave(k)]

    @property
    def codigos_material(self) -> list[str]:
        """Códigos de material sin repetir, en el orden del catálogo."""
        return list(dict.fromkeys(m.material for m in self.materiales))


class Catalogo(BaseModel):
    productos: list[ProductoCatalogo] = Field(min_length=1)

    @field_validator("productos")
    @classmethod
    def _nombres_unicos(cls, productos: list[ProductoCatalogo]) -> list[ProductoCatalogo]:
        nombres = [p.nombre.lower() for p in productos]
        repetidos = {n for n in nombres if nombres.count(n) > 1}
        if repetidos:
            raise ValueError(f"productos repetidos: {sorted(repetidos)}")
        return productos


def cargar_catalogo(ruta: Path = RUTA_CATALOGO) -> Catalogo:
    """Lee y valida el catálogo. Falla al arrancar si el JSON tiene errores."""
    with ruta.open(encoding="utf-8") as archivo:
        return Catalogo.model_validate(json.load(archivo))


@lru_cache
def obtener_catalogo() -> Catalogo:
    return cargar_catalogo()
