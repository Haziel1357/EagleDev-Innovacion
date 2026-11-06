"""Pruebas de la API de necesidades de materiales."""

from fastapi.testclient import TestClient

URL = "/api/v1/necesidades"


def test_publicar_y_consultar(client: TestClient, crear_empresa, publicar_necesidad) -> None:
    empresa = crear_empresa("demanda@x.co")

    necesidad = publicar_necesidad(empresa, dimensiones_minimas={"largo_cm": 30})
    detalle = client.get(f"{URL}/{necesidad['id']}")

    assert necesidad["estado"] == "ABIERTA"
    assert necesidad["categoria"]["codigo"] == "madera"
    assert necesidad["dimensiones_minimas"]["largo_cm"] == 30
    assert detalle.status_code == 200
    assert detalle.json()["titulo"] == "Necesito madera para marcos"


def test_publicar_requiere_sesion_y_empresa(client: TestClient, registrar, categoria_id) -> None:
    cuerpo = {
        "categoria_id": categoria_id("madera"),
        "titulo": "Necesito madera",
        "cantidad": "5",
        "unidad_medida": "UNIDAD",
    }

    sin_sesion = client.post(URL, json=cuerpo)
    sin_empresa = client.post(URL, json=cuerpo, headers=registrar())

    assert sin_sesion.status_code == 401
    assert sin_empresa.status_code == 409


def test_datos_invalidos(client: TestClient, crear_empresa, categoria_id) -> None:
    empresa = crear_empresa("demanda@x.co")
    cuerpo = {
        "categoria_id": categoria_id("madera"),
        "titulo": "Necesito madera",
        "cantidad": "0",
        "unidad_medida": "UNIDAD",
    }

    cantidad_cero = client.post(URL, headers=empresa, json=cuerpo)
    categoria_inexistente = client.post(
        URL, headers=empresa, json={**cuerpo, "cantidad": "5", "categoria_id": 9999}
    )

    assert cantidad_cero.status_code == 422
    assert cantidad_cero.json()["detalles"][0]["campo"].endswith("cantidad")
    assert categoria_inexistente.status_code == 404


def test_listado_publico_solo_muestra_abiertas(
    client: TestClient, crear_empresa, publicar_necesidad
) -> None:
    empresa = crear_empresa("demanda@x.co")
    abierta = publicar_necesidad(empresa)
    cerrada = publicar_necesidad(empresa, titulo="Necesito tela", categoria="tela")
    client.delete(f"{URL}/{cerrada['id']}", headers=empresa)

    publicas = client.get(URL).json()
    cerradas = client.get(URL, params={"estado": "CERRADA"}).json()
    de_tela = client.get(URL, params={"texto": "tela", "estado": "CERRADA"}).json()

    assert [n["id"] for n in publicas["elementos"]] == [abierta["id"]]
    assert [n["id"] for n in cerradas["elementos"]] == [cerrada["id"]]
    assert de_tela["total"] == 1


def test_mis_necesidades_incluye_todos_los_estados(
    client: TestClient, crear_empresa, publicar_necesidad
) -> None:
    empresa = crear_empresa("demanda@x.co")
    publicar_necesidad(empresa)
    cerrada = publicar_necesidad(empresa, titulo="Otra necesidad")
    client.delete(f"{URL}/{cerrada['id']}", headers=empresa)
    publicar_necesidad(crear_empresa("otra@x.co"))

    mias = client.get(f"{URL}/mias", headers=empresa).json()
    solo_cerradas = client.get(f"{URL}/mias", headers=empresa, params={"estado": "CERRADA"}).json()

    assert mias["total"] == 2
    assert solo_cerradas["total"] == 1


def test_actualizar_y_cambiar_estado(
    client: TestClient, crear_empresa, publicar_necesidad, categoria_id
) -> None:
    empresa = crear_empresa("demanda@x.co")
    necesidad = publicar_necesidad(empresa)

    actualizada = client.put(
        f"{URL}/{necesidad['id']}",
        headers=empresa,
        json={
            "categoria_id": categoria_id("metal"),
            "titulo": "Necesito láminas de metal",
            "cantidad": "3",
            "unidad_medida": "KILOGRAMO",
        },
    )
    atendida = client.patch(
        f"{URL}/{necesidad['id']}/estado", headers=empresa, json={"estado": "ATENDIDA"}
    )

    assert actualizada.status_code == 200
    assert actualizada.json()["categoria"]["codigo"] == "metal"
    assert actualizada.json()["unidad_medida"] == "KILOGRAMO"
    assert atendida.json()["estado"] == "ATENDIDA"


def test_cerrar_conserva_el_registro(client: TestClient, crear_empresa, publicar_necesidad) -> None:
    empresa = crear_empresa("demanda@x.co")
    necesidad = publicar_necesidad(empresa)

    borrado = client.delete(f"{URL}/{necesidad['id']}", headers=empresa)
    detalle = client.get(f"{URL}/{necesidad['id']}").json()

    assert borrado.status_code == 204
    assert detalle["estado"] == "CERRADA"


def test_no_se_puede_modificar_una_necesidad_ajena(
    client: TestClient, crear_empresa, publicar_necesidad
) -> None:
    necesidad = publicar_necesidad(crear_empresa("demanda@x.co"))
    intruso = crear_empresa("intruso@x.co")

    estado = client.patch(
        f"{URL}/{necesidad['id']}/estado", headers=intruso, json={"estado": "CERRADA"}
    )
    borrado = client.delete(f"{URL}/{necesidad['id']}", headers=intruso)
    inexistente = client.get(f"{URL}/9999")

    assert estado.status_code == 403
    assert borrado.status_code == 403
    assert inexistente.status_code == 404
