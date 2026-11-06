"""Pruebas del registro y consulta de empresas."""

from fastapi.testclient import TestClient

EMPRESA = {
    "nombre": "Muebles El Roble",
    "identificacion": "900123456-1",
    "tipo": "PEQUENA_EMPRESA",
    "ubicacion": {"ciudad": "Medellín", "latitud": 6.25, "longitud": -75.56},
}


def test_registrar_y_consultar_mi_empresa(client: TestClient, registrar) -> None:
    cabeceras = registrar()
    actividades = client.get("/api/v1/empresas/actividades").json()

    creada = client.post(
        "/api/v1/empresas",
        headers=cabeceras,
        json={**EMPRESA, "actividad_economica_id": actividades[0]["id"]},
    )
    mia = client.get("/api/v1/empresas/mia", headers=cabeceras)
    perfil = client.get("/api/v1/usuarios/me", headers=cabeceras)

    assert creada.status_code == 201
    assert creada.json()["actividad_economica"]["codigo"] == actividades[0]["codigo"]
    assert mia.json()["id"] == creada.json()["id"]
    assert perfil.json()["empresa_id"] == creada.json()["id"]


def test_una_empresa_por_cuenta_e_identificacion_unica(client: TestClient, registrar) -> None:
    cabeceras = registrar()
    client.post("/api/v1/empresas", headers=cabeceras, json=EMPRESA)

    repetida = client.post("/api/v1/empresas", headers=cabeceras, json=EMPRESA)
    otra_cuenta = client.post("/api/v1/empresas", headers=registrar("otro@x.co"), json=EMPRESA)

    assert repetida.status_code == 409
    assert otra_cuenta.status_code == 409


def test_sin_empresa_no_hay_mia(client: TestClient, registrar) -> None:
    respuesta = client.get("/api/v1/empresas/mia", headers=registrar())

    assert respuesta.status_code == 409
    assert "empresa" in respuesta.json()["mensaje"]


def test_solo_el_dueno_actualiza(client: TestClient, registrar) -> None:
    dueno = registrar()
    empresa = client.post("/api/v1/empresas", headers=dueno, json=EMPRESA).json()

    ajeno = client.put(
        f"/api/v1/empresas/{empresa['id']}", headers=registrar("otro@x.co"), json=EMPRESA
    )
    propio = client.put(
        f"/api/v1/empresas/{empresa['id']}",
        headers=dueno,
        json={**EMPRESA, "nombre": "El Roble SAS", "ubicacion": {"ciudad": "Envigado"}},
    )

    assert ajeno.status_code == 403
    assert propio.status_code == 200
    assert propio.json()["nombre"] == "El Roble SAS"
    assert propio.json()["ubicacion"]["ciudad"] == "Envigado"


def test_listar_empresas_con_filtros(client: TestClient, crear_empresa) -> None:
    crear_empresa("a@x.co", nombre="Textiles Andinos", ciudad="Cali")
    crear_empresa("b@x.co", nombre="Cartones del Sur", ciudad="Pasto")

    por_ciudad = client.get("/api/v1/empresas", params={"ciudad": "cali"}).json()
    por_texto = client.get("/api/v1/empresas", params={"texto": "carton"}).json()

    assert [e["nombre"] for e in por_ciudad["elementos"]] == ["Textiles Andinos"]
    assert por_texto["total"] == 1
