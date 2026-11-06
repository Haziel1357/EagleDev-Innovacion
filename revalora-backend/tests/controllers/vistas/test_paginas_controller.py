"""Pruebas de las páginas HTML (vistas Jinja2 bajo /app)."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.security.usuario_autenticado import COOKIE_TOKEN


def _iniciar_sesion(client: TestClient, cabeceras: dict[str, str]) -> None:
    """Las vistas usan la cookie de sesión, como el navegador."""
    client.cookies.set(COOKIE_TOKEN, cabeceras["Authorization"].removeprefix("Bearer "))


@pytest.mark.parametrize(
    "ruta",
    [
        "/",
        "/app/ingresar",
        "/app/registro",
        "/app/materiales",
        "/app/materiales/1",
        "/app/empresas/1",
        "/app/necesidades",
        "/app/necesidades/1",
    ],
)
def test_paginas_publicas_responden_html(client: TestClient, ruta: str) -> None:
    respuesta = client.get(ruta)

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "window.REVALORA" in respuesta.text


PAGINAS_CON_EMPRESA = (
    "/app/materiales/publicar",
    "/app/materiales/1/editar",
    "/app/mis-materiales",
    "/app/necesidades/publicar",
    "/app/necesidades/1/editar",
    "/app/mis-necesidades",
    "/app/solicitudes",
    "/app/solicitudes/1",
    "/app/historial",
    "/app/coincidencias",
    "/app/oportunidades",
    "/app/oportunidades/1",
)


def test_buscador_requiere_sesion_pero_no_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    sin_sesion = client.get("/app/buscador", follow_redirects=False)
    assert sin_sesion.status_code == 303
    assert sin_sesion.headers["location"] == "/app/ingresar?siguiente=/app/buscador"

    _iniciar_sesion(client, registrar())
    respuesta = client.get("/app/buscador")

    assert respuesta.status_code == 200
    assert "Usar mi ubicación" in respuesta.text


@pytest.mark.parametrize("ruta", ["/app/perfil", "/app/empresa", *PAGINAS_CON_EMPRESA])
def test_paginas_privadas_sin_sesion_redirigen_al_ingreso(client: TestClient, ruta: str) -> None:
    respuesta = client.get(ruta, follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == f"/app/ingresar?siguiente={ruta}"


def test_cookie_invalida_se_trata_como_sin_sesion(client: TestClient) -> None:
    client.cookies.set(COOKIE_TOKEN, "token-falso")

    respuesta = client.get("/app/materiales")

    assert respuesta.status_code == 200
    assert "Ingresar" in respuesta.text


def test_publicar_sin_empresa_redirige_al_registro_de_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, registrar())

    respuesta = client.get("/app/materiales/publicar", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/app/empresa?siguiente=/app/materiales/publicar"
    assert client.get("/app/empresa").status_code == 200


def test_con_empresa_se_ven_las_paginas_privadas(
    client: TestClient, crear_empresa: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, crear_empresa("taller@demo.co", nombre="Taller Demo"))

    for ruta in (*PAGINAS_CON_EMPRESA, "/app/perfil", "/app/empresa"):
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "Taller Demo" in respuesta.text or "Mi empresa" in respuesta.text


def test_solicitudes_sin_empresa_redirigen_al_registro_de_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, registrar())

    respuesta = client.get("/app/solicitudes", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/app/empresa?siguiente=/app/solicitudes"


def test_con_sesion_ingresar_redirige_al_catalogo(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, registrar())

    respuesta = client.get("/app/ingresar", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/app/materiales"
