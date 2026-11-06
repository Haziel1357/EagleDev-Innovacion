"""Pruebas del buscador inteligente y de la búsqueda tradicional."""

from fastapi.testclient import TestClient

from app.exceptions import IaServiceError


def test_busca_materiales_para_un_producto(
    client: TestClient, crear_empresa, publicar_material, ia
) -> None:
    lejos = crear_empresa("lejos@x.co", latitud=6.25, longitud=-75.56)
    cerca = crear_empresa("cerca@x.co", latitud=4.66, longitud=-74.06)
    publicar_material(lejos, titulo="Madera lejana", precio="1000")
    publicar_material(cerca, titulo="Madera cercana", precio="1000")
    publicar_material(
        cerca, categoria="carton", titulo="Cartón grueso", tipo_oferta="APROVECHAMIENTO"
    )
    usuario = crear_empresa("artesano@x.co", latitud=4.65, longitud=-74.05)

    respuesta = client.post(
        "/api/v1/buscador/inteligente",
        headers=usuario,
        json={"descripcion": "Quiero fabricar marcos para cuadros"},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["producto_interpretado"] == "marco para cuadros"
    por_material = {r["material"]: r for r in cuerpo["materiales_requeridos"]}
    assert list(por_material) == ["madera", "vidrio", "carton"]
    assert [r["material"]["titulo"] for r in por_material["madera"]["resultados"]] == [
        "Madera cercana",
        "Madera lejana",
    ]
    assert por_material["madera"]["funcion"] == "estructura"
    assert por_material["vidrio"]["resultados"] == []
    assert por_material["carton"]["resultados"][0]["material"]["distancia_km"] < 5
    assert cuerpo["total_resultados"] == 3
    assert ia.llamadas == [("recomendacion", "Quiero fabricar marcos para cuadros")]


def test_material_desconocido_para_la_plataforma(client: TestClient, registrar, ia) -> None:
    ia.recomendacion.materiales[0].material = "Fibra de carbono"

    cuerpo = client.post(
        "/api/v1/buscador/inteligente", headers=registrar(), json={"descripcion": "una bicicleta"}
    ).json()

    assert cuerpo["materiales_requeridos"][0]["material"] == "fibra de carbono"
    assert cuerpo["materiales_requeridos"][0]["categoria"] is None


def test_historial_de_busquedas(client: TestClient, registrar) -> None:
    cabeceras = registrar()
    client.post(
        "/api/v1/buscador/inteligente", headers=cabeceras, json={"descripcion": "marcos de fotos"}
    )

    historial = client.get("/api/v1/buscador/inteligente/historial", headers=cabeceras).json()
    detalle = client.get(
        f"/api/v1/buscador/inteligente/historial/{historial['elementos'][0]['id']}",
        headers=cabeceras,
    )

    assert historial["total"] == 1
    assert len(detalle.json()["materiales_requeridos"]) == 3
    assert (
        client.get(
            f"/api/v1/buscador/inteligente/historial/{historial['elementos'][0]['id']}",
            headers=registrar("otro@x.co"),
        ).status_code
        == 403
    )


def test_si_la_ia_falla_responde_502(client: TestClient, registrar, ia) -> None:
    ia.error = IaServiceError("El servicio de IA no respondió a tiempo.")
    cabeceras = registrar()

    respuesta = client.post(
        "/api/v1/buscador/inteligente", headers=cabeceras, json={"descripcion": "marcos"}
    )

    assert respuesta.status_code == 502
    assert (
        client.get("/api/v1/buscador/inteligente/historial", headers=cabeceras).json()["total"] == 0
    )


def test_busqueda_tradicional_excluye_lo_propio_y_ordena(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    yo = crear_empresa("yo@x.co", latitud=4.65, longitud=-74.05)
    publicar_material(yo, titulo="Mi madera")
    otro = crear_empresa("otro@x.co", latitud=4.60, longitud=-74.10)
    publicar_material(otro, titulo="Madera cara", precio="9000")
    publicar_material(otro, titulo="Madera barata", precio="100")

    anonimo = client.get("/api/v1/buscador/tradicional", params={"texto": "madera"}).json()
    con_sesion = client.get(
        "/api/v1/buscador/tradicional", headers=yo, params={"orden": "precio", "radio_km": 20}
    ).json()
    sin_coordenadas = client.get("/api/v1/buscador/tradicional", params={"orden": "cercania"})

    assert anonimo["total"] == 3
    assert [m["titulo"] for m in con_sesion["elementos"]] == ["Madera barata", "Madera cara"]
    assert all(m["distancia_km"] is not None for m in con_sesion["elementos"])
    assert sin_coordenadas.status_code == 422


def test_radio_sin_coordenadas_es_invalido(client: TestClient) -> None:
    assert client.get("/api/v1/buscador/tradicional", params={"radio_km": 10}).status_code == 422
    assert client.get("/api/v1/materiales", params={"radio_km": 10}).status_code == 422
