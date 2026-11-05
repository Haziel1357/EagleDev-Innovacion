"""Pruebas del controlador de materiales sobrantes."""

from fastapi.testclient import TestClient

from tests.conftest import PNG_1X1


def test_publicar_requiere_empresa(client: TestClient, registrar, categoria_id) -> None:
    respuesta = client.post(
        "/materiales",
        headers=registrar(),
        json={
            "categoria_id": categoria_id("madera"),
            "titulo": "Retazos",
            "cantidad": "5",
            "unidad_medida": "UNIDAD",
            "estado": "BUENO",
            "tipo_oferta": "APROVECHAMIENTO",
        },
    )

    assert respuesta.status_code == 409


def test_publicar_y_consultar_material(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    cabeceras = crear_empresa("a@x.co", nombre="Muebles El Roble")

    material = publicar_material(cabeceras, dimensiones={"largo_cm": 120, "ancho_cm": 30})
    detalle = client.get(f"/materiales/{material['id']}").json()

    assert detalle["categoria"]["codigo"] == "madera"
    assert detalle["disponibilidad"] == "DISPONIBLE"
    assert detalle["verificado_ia"] is False
    assert detalle["dimensiones"] == {"largo_cm": 120.0, "ancho_cm": 30.0, "alto_cm": None}
    assert detalle["empresa"]["nombre"] == "Muebles El Roble"


def test_venta_sin_precio_es_invalida(client: TestClient, crear_empresa, categoria_id) -> None:
    respuesta = client.post(
        "/materiales",
        headers=crear_empresa("a@x.co"),
        json={
            "categoria_id": categoria_id("madera"),
            "titulo": "Retazos",
            "cantidad": "5",
            "unidad_medida": "UNIDAD",
            "estado": "BUENO",
            "tipo_oferta": "VENTA",
        },
    )

    assert respuesta.status_code == 422


def test_listado_filtra_y_oculta_retirados(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    cabeceras = crear_empresa("a@x.co")
    madera = publicar_material(cabeceras)
    publicar_material(cabeceras, categoria="tela", titulo="Retazos de lona")

    client.delete(f"/materiales/{madera['id']}", headers=cabeceras)
    publicos = client.get("/materiales").json()
    mios = client.get("/materiales/mios", headers=cabeceras).json()

    assert [m["titulo"] for m in publicos["elementos"]] == ["Retazos de lona"]
    assert mios["total"] == 2
    assert client.get(f"/materiales/{madera['id']}").status_code == 404
    assert client.get(f"/materiales/{madera['id']}", headers=cabeceras).status_code == 200


def test_solo_el_dueno_modifica(
    client: TestClient, crear_empresa, publicar_material, categoria_id
) -> None:
    dueno = crear_empresa("a@x.co")
    material = publicar_material(dueno)
    otro = crear_empresa("b@x.co")
    cambios = {
        "categoria_id": categoria_id("madera"),
        "titulo": "Retazos de pino seco",
        "cantidad": "15",
        "unidad_medida": "UNIDAD",
        "estado": "REGULAR",
        "tipo_oferta": "INTERCAMBIO",
    }

    ajeno = client.put(f"/materiales/{material['id']}", headers=otro, json=cambios)
    propio = client.put(f"/materiales/{material['id']}", headers=dueno, json=cambios)
    disponibilidad = client.patch(
        f"/materiales/{material['id']}/disponibilidad",
        headers=dueno,
        json={"disponibilidad": "RESERVADO"},
    )

    assert ajeno.status_code == 403
    assert propio.json()["tipo_oferta"] == "INTERCAMBIO"
    assert disponibilidad.json()["disponibilidad"] == "RESERVADO"


def test_subir_y_eliminar_fotos(
    client: TestClient, crear_empresa, publicar_material, uploads_temporales
) -> None:
    cabeceras = crear_empresa("a@x.co")
    material = publicar_material(cabeceras)
    url = f"/materiales/{material['id']}/fotos"

    subida = client.post(
        url,
        headers=cabeceras,
        files=[
            ("fotos", ("a.png", PNG_1X1, "image/png")),
            ("fotos", ("b.png", PNG_1X1, "image/png")),
        ],
    )
    fotos = subida.json()
    archivos = list((uploads_temporales / "materiales").iterdir())
    client.delete(f"{url}/{fotos[0]['id']}", headers=cabeceras)
    detalle = client.get(f"/materiales/{material['id']}").json()

    assert subida.status_code == 201
    assert [f["es_principal"] for f in fotos] == [True, False]
    assert len(archivos) == 2
    assert len(detalle["fotos"]) == 1
    assert detalle["fotos"][0]["es_principal"] is True
    assert len(list((uploads_temporales / "materiales").iterdir())) == 1


def test_rechaza_archivo_que_no_es_imagen(
    client: TestClient, crear_empresa, publicar_material
) -> None:
    cabeceras = crear_empresa("a@x.co")
    material = publicar_material(cabeceras)

    falso = client.post(
        f"/materiales/{material['id']}/fotos",
        headers=cabeceras,
        files=[("fotos", ("x.png", b"no soy una imagen", "image/png"))],
    )
    tipo = client.post(
        f"/materiales/{material['id']}/fotos",
        headers=cabeceras,
        files=[("fotos", ("x.pdf", b"%PDF-1.4", "application/pdf"))],
    )

    assert falso.status_code == 400
    assert tipo.status_code == 400
