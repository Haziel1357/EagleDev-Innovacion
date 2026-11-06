"""Pruebas de las páginas HTML (vistas Jinja2 sin prefijo; la API va en /api/v1)."""

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
        "/ingresar",
        "/registro",
        "/materiales",
        "/materiales/1",
        "/empresas/1",
        "/necesidades",
        "/necesidades/1",
    ],
)
def test_paginas_publicas_responden_html(client: TestClient, ruta: str) -> None:
    respuesta = client.get(ruta)

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "window.REVALORA" in respuesta.text


PAGINAS_CON_EMPRESA = (
    "/materiales/publicar",
    "/materiales/1/editar",
    "/mis-materiales",
    "/necesidades/publicar",
    "/necesidades/1/editar",
    "/mis-necesidades",
    "/solicitudes",
    "/solicitudes/1",
    "/historial",
    "/coincidencias",
    "/oportunidades",
    "/oportunidades/1",
)


def test_buscador_requiere_sesion_pero_no_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    sin_sesion = client.get("/buscador", follow_redirects=False)
    assert sin_sesion.status_code == 303
    assert sin_sesion.headers["location"] == "/ingresar?siguiente=/buscador"

    _iniciar_sesion(client, registrar())
    respuesta = client.get("/buscador")

    assert respuesta.status_code == 200
    assert "Usar mi ubicación" in respuesta.text


@pytest.mark.parametrize("ruta", ["/perfil", "/empresa", *PAGINAS_CON_EMPRESA])
def test_paginas_privadas_sin_sesion_redirigen_al_ingreso(client: TestClient, ruta: str) -> None:
    respuesta = client.get(ruta, follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == f"/ingresar?siguiente={ruta}"


def test_cookie_invalida_se_trata_como_sin_sesion(client: TestClient) -> None:
    client.cookies.set(COOKIE_TOKEN, "token-falso")

    respuesta = client.get("/materiales")

    assert respuesta.status_code == 200
    assert "Ingresar" in respuesta.text


def test_publicar_sin_empresa_redirige_al_registro_de_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, registrar())

    respuesta = client.get("/materiales/publicar", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/empresa?siguiente=/materiales/publicar"
    assert client.get("/empresa").status_code == 200


def test_con_empresa_se_ven_las_paginas_privadas(
    client: TestClient, crear_empresa: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, crear_empresa("taller@demo.co", nombre="Taller Demo"))

    for ruta in (*PAGINAS_CON_EMPRESA, "/perfil", "/empresa"):
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "Taller Demo" in respuesta.text or "Mi empresa" in respuesta.text


def test_solicitudes_sin_empresa_redirigen_al_registro_de_empresa(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, registrar())

    respuesta = client.get("/solicitudes", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/empresa?siguiente=/solicitudes"


def test_con_sesion_ingresar_redirige_al_catalogo(
    client: TestClient, registrar: Callable[..., dict[str, str]]
) -> None:
    _iniciar_sesion(client, registrar())

    respuesta = client.get("/ingresar", follow_redirects=False)

    assert respuesta.status_code == 303
    assert respuesta.headers["location"] == "/materiales"
