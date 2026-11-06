"""Pruebas de POST /api/v1/recomendacion y del análisis de la descripción."""

import pytest
from fastapi.testclient import TestClient

from app.ml.recomendacion.analizador_producto import AnalizadorProducto
from app.ml.recomendacion.catalogo import obtener_catalogo
from app.utils.texto_utils import formas_singulares, palabras
from tests.conftest import URL

RUTA = f"{URL}/recomendacion"


def _recomendar(client: TestClient, descripcion: str) -> dict:
    respuesta = client.post(RUTA, json={"descripcion": descripcion})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()


def test_ejemplo_del_contrato(client: TestClient) -> None:
    cuerpo = _recomendar(client, "Quiero fabricar marcos para cuadros")

    assert cuerpo["producto"] == "Marco para cuadros"
    assert [m["material"] for m in cuerpo["materiales"]] == ["madera", "vidrio", "carton"]
    madera = cuerpo["materiales"][0]
    assert madera == {
        "material": "madera",
        "funcion": "estructura del marco",
        "cantidad_estimada": 2.0,
        "unidad": "METRO",
    }


@pytest.mark.parametrize(
    ("descripcion", "producto"),
    [
        ("Lámparas para restaurante", "Lámpara decorativa"),  # tilde y plural
        ("COJINES PARA LA SALA", "Cojín decorativo"),  # mayúsculas, plural en -es
        ("portalápices para oficina", "Portalápices"),  # plural en -ces
        ("una mesa de centro con estibas", "Mesa de palets"),
        ("repisas para la cocina", "Repisa o estantería"),
        ("bolsos de jean", "Bolsa reutilizable"),
        ("cajas de envío para mi tienda", "Empaque y relleno para envíos"),  # frase gana a palabra
    ],
)
def test_reconoce_productos(client: TestClient, descripcion: str, producto: str) -> None:
    assert _recomendar(client, descripcion)["producto"] == producto


def test_los_materiales_principales_van_primero(client: TestClient) -> None:
    catalogo = {p.nombre: p for p in obtener_catalogo().productos}
    cuerpo = _recomendar(client, "una lámpara")

    principales = {m.material for m in catalogo["Lámpara decorativa"].materiales if m.principal}
    primeros = {m["material"] for m in cuerpo["materiales"][: len(principales)]}
    assert primeros == principales


def test_agrega_los_materiales_mencionados(client: TestClient) -> None:
    cuerpo = _recomendar(client, "Una lámpara hecha con botellas de plástico")

    ultimo = cuerpo["materiales"][-1]
    assert ultimo == {
        "material": "plastico",
        "funcion": "indicado en la descripción",
        "cantidad_estimada": None,
        "unidad": None,
    }


def test_sin_producto_devuelve_solo_los_materiales_mencionados(client: TestClient) -> None:
    cuerpo = _recomendar(client, "algo con botellas de plástico y lona")

    assert cuerpo["producto"] is None
    assert [m["material"] for m in cuerpo["materiales"]] == ["plastico", "tela"]


def test_texto_sin_sentido(client: TestClient) -> None:
    assert _recomendar(client, "asdf qwerty") == {"producto": None, "materiales": []}


@pytest.mark.parametrize("descripcion", ["", "ab", "x" * 1001])
def test_descripcion_invalida_responde_422(client: TestClient, descripcion: str) -> None:
    respuesta = client.post(RUTA, json={"descripcion": descripcion})

    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "body.descripcion"


# ------------------------------------------------------------------- análisis del texto


def test_material_especifico_gana_al_generico() -> None:
    """'botellas de vidrio' no debe detectar plástico por la palabra 'botella'."""
    analizador = AnalizadorProducto(obtener_catalogo())

    assert analizador.analizar("botellas de vidrio").materiales_mencionados == ["vidrio"]
    assert analizador.analizar("botellas").materiales_mencionados == ["plastico"]
    # "retazo" no implica tela: son restos de cualquier material.
    assert analizador.analizar("retazos de MDF y aluminio").materiales_mencionados == [
        "madera",
        "metal",
    ]


def test_normalizacion_del_texto() -> None:
    assert palabras("¡Quiero fabricar Lámparas, por favor!") == ["lamparas", "favor"]
    assert {"lampara"} <= formas_singulares("lamparas")
    assert {"cojin"} <= formas_singulares("cojines")
    assert {"lapiz"} <= formas_singulares("lapices")
    assert {"estante"} <= formas_singulares("estantes")
    assert formas_singulares("mes") == {"mes"}  # palabras cortas no se recortan
