"""Pruebas de solicitudes de compra o intercambio y del historial de operaciones."""

from fastapi.testclient import TestClient


def _solicitar(client: TestClient, cabeceras, material_id: int, **datos):
    cuerpo = {"material_id": material_id, "tipo": "COMPRA", "cantidad": "5", **datos}
    return client.post("/api/v1/solicitudes", headers=cabeceras, json=cuerpo)


def test_flujo_completo_de_compra(client: TestClient, crear_empresa, publicar_material) -> None:
    vendedor = crear_empresa("vende@x.co")
    material = publicar_material(vendedor, cantidad="20")
    comprador = crear_empresa("compra@x.co")

    solicitud = _solicitar(client, comprador, material["id"], mensaje="¿Lo recojo el lunes?").json()
    recibidas = client.get("/api/v1/solicitudes/recibidas", headers=vendedor).json()
    aceptada = client.post(
        f"/api/v1/solicitudes/{solicitud['id']}/aceptar",
        headers=vendedor,
        json={"comentario": "Listo"},
    ).json()
    completada = client.post(
        f"/api/v1/solicitudes/{solicitud['id']}/completar", headers=comprador
    ).json()
    historial = client.get(
        f"/api/v1/historial/solicitudes/{solicitud['id']}", headers=vendedor
    ).json()

    assert solicitud["estado"] == "PENDIENTE"
    assert recibidas["total"] == 1
    assert aceptada["estado"] == "ACEPTADA"
    assert aceptada["material"]["cantidad"] == "15.000"
    assert completada["estado"] == "COMPLETADA"
    assert [(h["estado_anterior"], h["estado_nuevo"]) for h in historial] == [
        (None, "PENDIENTE"),
        ("PENDIENTE", "ACEPTADA"),
        ("ACEPTADA", "COMPLETADA"),
    ]
    assert client.get("/api/v1/historial", headers=comprador).json()["total"] == 3


def test_reglas_al_crear(client: TestClient, crear_empresa, publicar_material) -> None:
    vendedor = crear_empresa("vende@x.co")
    material = publicar_material(vendedor, cantidad="10")
    comprador = crear_empresa("compra@x.co")

    propio = _solicitar(client, vendedor, material["id"])
    tipo_incorrecto = _solicitar(client, comprador, material["id"], tipo="APROVECHAMIENTO")
    demasiado = _solicitar(client, comprador, material["id"], cantidad="11")
    primera = _solicitar(client, comprador, material["id"])
    duplicada = _solicitar(client, comprador, material["id"])

    assert propio.status_code == 409
    assert tipo_incorrecto.status_code == 409
    assert demasiado.status_code == 409
    assert primera.status_code == 201
    assert duplicada.status_code == 409


def test_solo_el_ofertante_responde_y_solo_el_solicitante_cancela(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    vendedor = crear_empresa("vende@x.co")
    material = publicar_material(vendedor)
    comprador = crear_empresa("compra@x.co")
    intruso = crear_empresa("intruso@x.co")
    solicitud = _solicitar(client, comprador, material["id"]).json()
    url = f"/api/v1/solicitudes/{solicitud['id']}"

    assert client.post(f"{url}/aceptar", headers=comprador).status_code == 403
    assert client.post(f"{url}/cancelar", headers=vendedor).status_code == 403
    assert client.get(url, headers=intruso).status_code == 403
    assert client.post(f"{url}/completar", headers=vendedor).status_code == 409

    cancelada = client.post(f"{url}/cancelar", headers=comprador)
    assert cancelada.json()["estado"] == "CANCELADA"
    assert client.post(f"{url}/rechazar", headers=vendedor).status_code == 409


def test_al_agotarse_se_rechazan_las_demas(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    vendedor = crear_empresa("vende@x.co")
    material = publicar_material(vendedor, cantidad="5")
    a = crear_empresa("a@x.co")
    b = crear_empresa("b@x.co")
    sol_a = _solicitar(client, a, material["id"], cantidad="5").json()
    sol_b = _solicitar(client, b, material["id"], cantidad="2").json()

    client.post(f"/api/v1/solicitudes/{sol_a['id']}/aceptar", headers=vendedor)
    estado_b = client.get(f"/api/v1/solicitudes/{sol_b['id']}", headers=b).json()
    detalle = client.get(f"/api/v1/materiales/{material['id']}").json()

    assert detalle["disponibilidad"] == "AGOTADO"
    assert estado_b["estado"] == "RECHAZADA"
    assert "automáticamente" in estado_b["historial"][-1]["comentario"]


def test_intercambio_reserva_el_material_ofrecido(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    a = crear_empresa("a@x.co")
    madera = publicar_material(a, tipo_oferta="INTERCAMBIO", precio=None)
    b = crear_empresa("b@x.co")
    tela = publicar_material(
        b, categoria="tela", titulo="Lona", tipo_oferta="INTERCAMBIO", precio=None
    )

    sin_material = _solicitar(client, b, madera["id"], tipo="INTERCAMBIO")
    ajeno = _solicitar(
        client, b, madera["id"], tipo="INTERCAMBIO", material_ofrecido_id=madera["id"]
    )
    solicitud = _solicitar(
        client, b, madera["id"], tipo="INTERCAMBIO", material_ofrecido_id=tela["id"]
    )
    client.post(f"/api/v1/solicitudes/{solicitud.json()['id']}/aceptar", headers=a)
    tela_despues = client.get(f"/api/v1/materiales/{tela['id']}").json()

    assert sin_material.status_code == 422
    assert ajeno.status_code == 404
    assert solicitud.status_code == 201
    assert solicitud.json()["material_ofrecido"]["id"] == tela["id"]
    assert tela_despues["disponibilidad"] == "RESERVADO"


def test_listas_filtradas_por_estado(client: TestClient, crear_empresa, publicar_material) -> None:
    vendedor = crear_empresa("vende@x.co")
    material = publicar_material(vendedor)
    comprador = crear_empresa("compra@x.co")
    solicitud = _solicitar(client, comprador, material["id"]).json()
    client.post(f"/api/v1/solicitudes/{solicitud['id']}/rechazar", headers=vendedor)

    pendientes = client.get(
        "/api/v1/solicitudes/enviadas", headers=comprador, params={"estado": "PENDIENTE"}
    )
    rechazadas = client.get(
        "/api/v1/solicitudes/enviadas", headers=comprador, params={"estado": "RECHAZADA"}
    )

    assert pendientes.json()["total"] == 0
    assert rechazadas.json()["total"] == 1
