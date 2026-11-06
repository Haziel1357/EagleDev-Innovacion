"""Pruebas de la API de coincidencias (el motor se ejecuta al publicar)."""

from fastapi.testclient import TestClient


def test_publicar_necesidad_crea_coincidencias(
    client: TestClient, crear_empresa, publicar_material, publicar_necesidad
) -> None:
    ofertante = crear_empresa("oferta@x.co")
    material = publicar_material(ofertante)
    publicar_material(ofertante, categoria="tela", titulo="Lona")
    demandante = crear_empresa("demanda@x.co", latitud=4.70, longitud=-74.10)

    necesidad = publicar_necesidad(demandante)
    de_necesidad = client.get(
        f"/api/v1/coincidencias/necesidades/{necesidad['id']}", headers=demandante
    ).json()
    del_ofertante = client.get("/api/v1/coincidencias", headers=ofertante).json()

    assert de_necesidad["total"] == 1
    coincidencia = de_necesidad["elementos"][0]
    assert coincidencia["material"]["id"] == material["id"]
    assert coincidencia["puntuacion"] > 90
    assert coincidencia["origen"] == "PUBLICACION_NECESIDAD"
    assert set(coincidencia["detalle"]) == {
        "material",
        "cantidad",
        "estado",
        "dimensiones",
        "ubicacion",
        "precio",
    }
    assert del_ofertante["total"] == 1


def test_publicar_material_despues_tambien_crea_coincidencias(
    client: TestClient, crear_empresa, publicar_material, publicar_necesidad
) -> None:
    demandante = crear_empresa("demanda@x.co")
    necesidad = publicar_necesidad(demandante)
    ofertante = crear_empresa("oferta@x.co")

    material = publicar_material(ofertante)
    coincidencias = client.get(
        f"/api/v1/coincidencias/materiales/{material['id']}", headers=ofertante
    ).json()

    assert coincidencias["elementos"][0]["necesidad"]["id"] == necesidad["id"]
    assert coincidencias["elementos"][0]["origen"] == "PUBLICACION_MATERIAL"


def test_no_cruza_con_la_propia_empresa_ni_materiales_retirados(
    client: TestClient, crear_empresa, publicar_material, publicar_necesidad
) -> None:
    empresa = crear_empresa("a@x.co")
    publicar_material(empresa)
    necesidad = publicar_necesidad(empresa)
    otra = crear_empresa("b@x.co")
    material = publicar_material(otra)

    antes = client.get(
        f"/api/v1/coincidencias/necesidades/{necesidad['id']}", headers=empresa
    ).json()
    client.delete(f"/api/v1/materiales/{material['id']}", headers=otra)
    despues = client.get(
        f"/api/v1/coincidencias/necesidades/{necesidad['id']}", headers=empresa
    ).json()

    assert antes["total"] == 1
    assert despues["total"] == 0


def test_cerrar_necesidad_borra_coincidencias_y_recalcular(
    client: TestClient, crear_empresa, publicar_material, publicar_necesidad
) -> None:
    ofertante = crear_empresa("oferta@x.co")
    publicar_material(ofertante)
    demandante = crear_empresa("demanda@x.co")
    necesidad = publicar_necesidad(demandante)

    client.patch(
        f"/api/v1/necesidades/{necesidad['id']}/estado",
        headers=demandante,
        json={"estado": "CERRADA"},
    )
    cerrada = client.get("/api/v1/coincidencias", headers=ofertante).json()
    client.patch(
        f"/api/v1/necesidades/{necesidad['id']}/estado",
        headers=demandante,
        json={"estado": "ABIERTA"},
    )
    recalculadas = client.post(
        f"/api/v1/coincidencias/necesidades/{necesidad['id']}/recalcular", headers=demandante
    ).json()

    assert cerrada["total"] == 0
    assert len(recalculadas) == 1
    assert recalculadas[0]["origen"] == "MANUAL"


def test_coincidencia_ajena_no_es_visible(
    client: TestClient, crear_empresa, publicar_material, publicar_necesidad
) -> None:
    publicar_material(crear_empresa("oferta@x.co"))
    demandante = crear_empresa("demanda@x.co")
    necesidad = publicar_necesidad(demandante)
    coincidencia = client.get(
        f"/api/v1/coincidencias/necesidades/{necesidad['id']}", headers=demandante
    ).json()
    intruso = crear_empresa("intruso@x.co")

    respuesta = client.get(
        f"/api/v1/coincidencias/{coincidencia['elementos'][0]['id']}", headers=intruso
    )
    ajena = client.get(f"/api/v1/coincidencias/necesidades/{necesidad['id']}", headers=intruso)

    assert respuesta.status_code == 403
    assert ajena.status_code == 403
