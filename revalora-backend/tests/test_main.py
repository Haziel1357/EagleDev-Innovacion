"""Pruebas de arranque de la aplicación y del manejo global de errores."""

from fastapi.testclient import TestClient

from app.exceptions import RecursoNoEncontradoError
from app.main import crear_app


def test_salud(client: TestClient) -> None:
    respuesta = client.get("/api/v1/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}


def test_inicio_renderiza_html(client: TestClient) -> None:
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "REVALORA" in respuesta.text


def test_ruta_inexistente_responde_json(client: TestClient) -> None:
    respuesta = client.get("/no-existe", headers={"accept": "application/json"})

    assert respuesta.status_code == 404
    assert respuesta.json()["ruta"] == "/no-existe"


def test_ruta_inexistente_desde_navegador_muestra_pagina(client: TestClient) -> None:
    respuesta = client.get("/no-existe", headers={"accept": "text/html"})

    assert respuesta.status_code == 404
    assert "Página no encontrada" in respuesta.text


def test_ruta_api_inexistente_responde_json_aunque_venga_del_navegador(
    client: TestClient,
) -> None:
    respuesta = client.get("/api/v1/no-existe", headers={"accept": "text/html"})

    assert respuesta.status_code == 404
    assert respuesta.headers["content-type"].startswith("application/json")
    assert respuesta.json()["ruta"] == "/api/v1/no-existe"


def test_rutas_de_api_tienen_prefijo(client: TestClient) -> None:
    """Toda ruta JSON va bajo /api/v1 para no chocar con las vistas HTML."""
    rutas = client.get("/openapi.json").json()["paths"]

    assert rutas
    assert all(ruta.startswith("/api/v1/") for ruta in rutas)


def test_error_de_negocio_usa_su_codigo_http() -> None:
    app = crear_app()

    @app.get("/prueba-error")
    def lanzar() -> None:
        raise RecursoNoEncontradoError("Material no encontrado.")

    respuesta = TestClient(app).get("/prueba-error")

    assert respuesta.status_code == 404
    assert respuesta.json()["mensaje"] == "Material no encontrado."
