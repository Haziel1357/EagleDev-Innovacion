"""Pruebas del reconocimiento de materiales."""

from fastapi.testclient import TestClient

from app.exceptions import IaServiceError
from tests.conftest import PNG_1X1


def _reconocer(client: TestClient, cabeceras: dict[str, str]):
    return client.post(
        "/ia/reconocimiento",
        headers=cabeceras,
        files={"imagen": ("foto.png", PNG_1X1, "image/png")},
    )


def test_reconoce_la_foto_y_queda_pendiente(
    client: TestClient, registrar, ia, uploads_temporales
) -> None:
    respuesta = _reconocer(client, registrar())

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["material_predicho"] == "madera"
    assert cuerpo["categoria_predicha"]["codigo"] == "madera"
    assert cuerpo["confianza"] == 0.93
    assert cuerpo["confianza_baja"] is False
    assert cuerpo["estado_verificacion"] == "PENDIENTE"
    assert [p["material"] for p in cuerpo["predicciones"]] == ["madera", "carton"]
    assert all(p["categoria_id"] for p in cuerpo["predicciones"])
    assert cuerpo["imagen_url"].startswith("/uploads/reconocimientos/")
    assert ia.llamadas == [("reconocimiento", "image/png")]
    assert len(list((uploads_temporales / "reconocimientos").iterdir())) == 1


def test_confirmar_o_corregir(client: TestClient, registrar, categoria_id) -> None:
    cabeceras = registrar()
    primera = _reconocer(client, cabeceras).json()
    segunda = _reconocer(client, cabeceras).json()

    confirmada = client.post(
        f"/ia/clasificaciones/{primera['id']}/confirmar", headers=cabeceras, json={}
    ).json()
    corregida = client.post(
        f"/ia/clasificaciones/{segunda['id']}/confirmar",
        headers=cabeceras,
        json={"categoria_id": categoria_id("metal")},
    ).json()

    assert confirmada["estado_verificacion"] == "CONFIRMADA"
    assert confirmada["categoria_confirmada"]["codigo"] == "madera"
    assert corregida["estado_verificacion"] == "CORREGIDA"
    assert corregida["categoria_confirmada"]["codigo"] == "metal"


def test_publicar_con_el_reconocimiento_verifica_el_material(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    cabeceras = crear_empresa("a@x.co")
    clasificacion = _reconocer(client, cabeceras).json()

    material = publicar_material(cabeceras, clasificacion_id=clasificacion["id"])
    despues = client.get(f"/ia/clasificaciones/{clasificacion['id']}", headers=cabeceras).json()
    reutilizada = client.post(
        "/materiales",
        headers=cabeceras,
        json={
            "categoria_id": material["categoria"]["id"],
            "titulo": "Otro",
            "cantidad": "1",
            "unidad_medida": "UNIDAD",
            "estado": "BUENO",
            "tipo_oferta": "APROVECHAMIENTO",
            "clasificacion_id": clasificacion["id"],
        },
    )

    assert material["verificado_ia"] is True
    assert len(material["fotos"]) == 1 and material["fotos"][0]["es_principal"]
    assert material["fotos"][0]["url"].startswith("/uploads/materiales/")
    assert despues["estado_verificacion"] == "CONFIRMADA"
    assert despues["material_id"] == material["id"]
    assert reutilizada.status_code == 409


def test_publicar_con_otra_categoria_no_verifica(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    cabeceras = crear_empresa("a@x.co")
    clasificacion = _reconocer(client, cabeceras).json()

    material = publicar_material(
        cabeceras, categoria="plastico", clasificacion_id=clasificacion["id"]
    )
    despues = client.get(f"/ia/clasificaciones/{clasificacion['id']}", headers=cabeceras).json()

    assert material["verificado_ia"] is False
    assert despues["estado_verificacion"] == "CORREGIDA"


def test_material_no_reconocido_por_la_plataforma(client: TestClient, registrar, ia) -> None:
    ia.reconocimiento.material = "ceramica"
    ia.reconocimiento.confianza = 0.4
    ia.reconocimiento.predicciones = []
    cabeceras = registrar()

    cuerpo = _reconocer(client, cabeceras).json()
    confirmar = client.post(
        f"/ia/clasificaciones/{cuerpo['id']}/confirmar", headers=cabeceras, json={}
    )

    assert cuerpo["categoria_predicha"] is None
    assert cuerpo["confianza_baja"] is True
    assert confirmar.status_code == 409


def test_si_la_ia_falla_no_se_guarda_nada(
    client: TestClient, registrar, ia, uploads_temporales
) -> None:
    ia.error = IaServiceError("No se pudo conectar con el servicio de IA.")
    cabeceras = registrar()

    respuesta = _reconocer(client, cabeceras)

    assert respuesta.status_code == 502
    assert client.get("/ia/clasificaciones", headers=cabeceras).json()["total"] == 0
    assert not (uploads_temporales / "reconocimientos").exists()


def test_clasificacion_ajena(client: TestClient, registrar) -> None:
    propia = _reconocer(client, registrar()).json()

    respuesta = client.get(f"/ia/clasificaciones/{propia['id']}", headers=registrar("otro@x.co"))

    assert respuesta.status_code == 403
