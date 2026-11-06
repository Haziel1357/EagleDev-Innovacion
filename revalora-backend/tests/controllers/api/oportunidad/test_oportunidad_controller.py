"""Pruebas de oportunidades productivas."""

from fastapi.testclient import TestClient

from app.schemas.ia_schema import RespuestaOportunidadesIA


def test_analiza_con_los_materiales_de_la_empresa(
    client: TestClient, crear_empresa, publicar_material, ia
) -> None:
    proveedor = crear_empresa("proveedor@x.co")
    publicar_material(proveedor, categoria="vidrio", titulo="Láminas de vidrio")
    empresa = crear_empresa("taller@x.co")
    publicar_material(empresa, categoria="madera")
    publicar_material(empresa, categoria="tela", titulo="Lona")
    ia.oportunidades = RespuestaOportunidadesIA(
        productos=[
            {
                "nombre": "Cojines",
                "viabilidad": 0.6,
                "materiales_utilizados": ["tela"],
                "materiales_faltantes": [{"material": "relleno"}],
            },
            {
                "nombre": "Marcos para cuadros",
                "viabilidad": 0.9,
                "materiales_utilizados": ["madera"],
                "materiales_faltantes": [{"material": "vidrio", "descripcion": "Para el frente"}],
            },
        ]
    )

    respuesta = client.post("/api/v1/oportunidades/analizar", headers=empresa, json={})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["materiales_analizados"] == ["madera", "tela"]
    assert [p["nombre"] for p in cuerpo["productos"]] == ["Marcos para cuadros", "Cojines"]
    vidrio = cuerpo["productos"][0]["materiales_faltantes"][0]
    assert vidrio["categoria"]["codigo"] == "vidrio"
    assert vidrio["disponibles_en_plataforma"] == 1
    relleno = cuerpo["productos"][1]["materiales_faltantes"][0]
    assert relleno["categoria"] is None and relleno["disponibles_en_plataforma"] == 0
    assert ia.llamadas == [("oportunidades", ["madera", "tela"])]

    lista = client.get("/api/v1/oportunidades", headers=empresa).json()
    assert lista["total"] == 1
    assert client.get(f"/api/v1/oportunidades/{cuerpo['id']}", headers=proveedor).status_code == 403


def test_sin_materiales_ni_categorias(client: TestClient, crear_empresa, categoria_id) -> None:
    empresa = crear_empresa("taller@x.co")

    sin_nada = client.post("/api/v1/oportunidades/analizar", headers=empresa, json={})
    con_categorias = client.post(
        "/api/v1/oportunidades/analizar",
        headers=empresa,
        json={"categoria_ids": [categoria_id("metal")]},
    )
    inexistente = client.post(
        "/api/v1/oportunidades/analizar", headers=empresa, json={"categoria_ids": [999]}
    )

    assert sin_nada.status_code == 409
    assert con_categorias.status_code == 201
    assert con_categorias.json()["materiales_analizados"] == ["metal"]
    assert inexistente.status_code == 404
