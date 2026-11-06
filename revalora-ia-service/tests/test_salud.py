"""Pruebas de arranque, salud y formato de errores."""

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import crear_app
from tests.conftest import URL


def test_salud_indica_el_modelo_en_uso(client: TestClient) -> None:
    respuesta = client.get(f"{URL}/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok", "modelo_vision": "heuristico"}


def test_carga_diferida_del_modelo() -> None:
    config = Settings(modelo_vision="heuristico", cargar_modelo_al_iniciar=False)

    with TestClient(crear_app(config)) as cliente:
        antes = cliente.get(f"{URL}/salud").json()["modelo_vision"]
        cliente.post(f"{URL}/recomendacion", json={"descripcion": "marcos"})
        # La recomendación no usa el modelo de visión: sigue sin cargar.
        intermedio = cliente.get(f"{URL}/salud").json()["modelo_vision"]

    assert antes == "sin_cargar"
    assert intermedio == "sin_cargar"


def test_todas_las_rutas_tienen_prefijo(client: TestClient) -> None:
    rutas = client.get("/openapi.json").json()["paths"]

    assert set(rutas) == {
        "/api/v1/salud",
        "/api/v1/reconocimiento",
        "/api/v1/recomendacion",
        "/api/v1/oportunidades",
    }


def test_ruta_inexistente_responde_con_el_formato_de_error(client: TestClient) -> None:
    respuesta = client.get(f"{URL}/no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json() == {
        "estado": 404,
        "error": "Not Found",
        "mensaje": "Not Found",
        "ruta": "/api/v1/no-existe",
    }
