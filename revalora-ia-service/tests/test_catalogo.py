"""Validación del catálogo de productos y de la lista de materiales.

Ejecuta este archivo después de editar catalogo_productos.json:
    uv run pytest tests/test_catalogo.py
"""

import json

import pytest

from app.ml.materiales import CODIGOS_MATERIAL, MATERIALES
from app.ml.recomendacion.catalogo import RUTA_CATALOGO, Catalogo, cargar_catalogo

# Códigos de categorias_material del backend (revalora-backend/app/utils/constantes.py).
CODIGOS_BACKEND = {"madera", "carton", "plastico", "tela", "metal", "vidrio", "papel", "otro"}


def test_los_materiales_coinciden_con_el_backend() -> None:
    assert CODIGOS_MATERIAL == CODIGOS_BACKEND
    for material in MATERIALES:
        assert material.descripciones_clip, material.codigo


def test_el_catalogo_es_valido() -> None:
    catalogo = cargar_catalogo()

    assert len(catalogo.productos) >= 20
    for producto in catalogo.productos:
        assert any(m.principal for m in producto.materiales), producto.nombre
        assert len(producto.codigos_material) == len(producto.materiales), producto.nombre


def test_todos_los_materiales_tienen_productos() -> None:
    usados = {m.material for p in cargar_catalogo().productos for m in p.materiales}

    assert usados == CODIGOS_MATERIAL - {"otro"}


@pytest.mark.parametrize(
    ("cambio", "error"),
    [
        ({"material": "oro"}, "material desconocido"),
        ({"unidad": "PULGADA"}, "unidad desconocida"),
    ],
)
def test_detecta_errores_en_el_catalogo(cambio: dict, error: str) -> None:
    datos = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))
    datos["productos"][0]["materiales"][0].update(cambio)

    with pytest.raises(ValueError, match=error):
        Catalogo.model_validate(datos)


def test_detecta_productos_repetidos() -> None:
    datos = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))
    datos["productos"].append(datos["productos"][0])

    with pytest.raises(ValueError, match="repetidos"):
        Catalogo.model_validate(datos)
