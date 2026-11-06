"""Pruebas de la aplicación web progresiva: manifest, service worker y página sin conexión."""

import json
import re

from fastapi.testclient import TestClient


def _precache(client: TestClient) -> list[str]:
    codigo = client.get("/sw.js").text
    return json.loads(re.search(r"const PRECACHE = (.*);", codigo).group(1))


def test_manifest_permite_instalar_la_app(client: TestClient) -> None:
    respuesta = client.get("/manifest.webmanifest")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("application/manifest+json")
    manifest = respuesta.json()
    assert manifest["short_name"] == "REVALORA"
    assert manifest["start_url"] == "/"
    assert manifest["scope"] == "/"
    assert manifest["display"] == "standalone"
    tamanos = {(icono["sizes"], icono["purpose"]) for icono in manifest["icons"]}
    assert {("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")} <= tamanos


def test_iconos_y_atajos_del_manifest_existen(client: TestClient) -> None:
    manifest = client.get("/manifest.webmanifest").json()

    for icono in manifest["icons"]:
        respuesta = client.get(icono["src"])
        assert respuesta.status_code == 200, icono["src"]
        assert respuesta.headers["content-type"] == "image/png"
    for atajo in manifest["shortcuts"]:
        assert client.get(atajo["url"], follow_redirects=False).status_code in {200, 303}


def test_service_worker_se_sirve_desde_la_raiz_sin_cache(client: TestClient) -> None:
    respuesta = client.get("/sw.js")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/javascript")
    assert respuesta.headers["cache-control"] == "no-cache"
    assert re.search(r'const VERSION = "[0-9a-f]{12}";', respuesta.text)


def test_todo_lo_que_precachea_el_service_worker_existe(client: TestClient) -> None:
    """Si una sola URL falla, el navegador no instala el service worker."""
    precache = _precache(client)

    assert "/sin-conexion" in precache
    for url in precache:
        assert client.get(url).status_code == 200, url


def test_pagina_sin_conexion_no_lleva_datos_de_sesion(client: TestClient) -> None:
    respuesta = client.get("/sin-conexion")

    assert respuesta.status_code == 200
    assert "Sin conexión" in respuesta.text
    assert "window.REVALORA" not in respuesta.text


def test_las_paginas_enlazan_el_manifest_y_registran_el_service_worker(
    client: TestClient,
) -> None:
    pagina = client.get("/").text

    assert 'rel="manifest"' in pagina
    assert 'rel="apple-touch-icon"' in pagina
    assert "js/pwa.js" in pagina
    assert 'serviceWorker: "/sw.js"' in pagina
