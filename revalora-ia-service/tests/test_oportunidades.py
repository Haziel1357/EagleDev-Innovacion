"""Pruebas de POST /api/v1/oportunidades."""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import URL

RUTA = f"{URL}/oportunidades"


def _sugerir(client: TestClient, materiales: list[str], max_productos: int = 5) -> list[dict]:
    respuesta = client.post(RUTA, json={"materiales": materiales, "max_productos": max_productos})
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.json()["productos"]


def test_ordena_por_viabilidad_y_usa_los_materiales(client: TestClient) -> None:
    productos = _sugerir(client, ["madera", "tela"], max_productos=20)

    assert productos
    viabilidades = [p["viabilidad"] for p in productos]
    assert viabilidades == sorted(viabilidades, reverse=True)
    for producto in productos:
        assert set(producto["materiales_utilizados"]) <= {"madera", "tela"}
        assert producto["materiales_utilizados"]
        faltantes = {f["material"] for f in producto["materiales_faltantes"]}
        assert not faltantes & {"madera", "tela"}
        assert all(f["descripcion"] for f in producto["materiales_faltantes"])


def test_viabilidad_pondera_los_materiales_principales(client: TestClient) -> None:
    productos = {p["nombre"]: p for p in _sugerir(client, ["madera"], max_productos=20)}

    # Marco: madera (principal, 3) de 3 + vidrio (1) + cartón (1) = 3/5
    assert productos["Marco para cuadros"]["viabilidad"] == 0.6
    assert [f["material"] for f in productos["Marco para cuadros"]["materiales_faltantes"]] == [
        "vidrio",
        "carton",
    ]
    assert productos["Juguete de madera"]["viabilidad"] == 1.0


def test_respeta_max_productos(client: TestClient) -> None:
    assert len(_sugerir(client, ["madera", "metal", "tela"], max_productos=2)) == 2


def test_normaliza_y_descarta_codigos_desconocidos(client: TestClient) -> None:
    assert _sugerir(client, [" Madera ", "xyz"]) == _sugerir(client, ["madera"])
    assert _sugerir(client, ["xyz"]) == []


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"materiales": []},
        {"materiales": ["madera"], "max_productos": 0},
        {"materiales": ["madera"], "max_productos": 21},
        {},
    ],
)
def test_peticion_invalida_responde_422(client: TestClient, cuerpo: dict) -> None:
    assert client.post(RUTA, json=cuerpo).status_code == 422
