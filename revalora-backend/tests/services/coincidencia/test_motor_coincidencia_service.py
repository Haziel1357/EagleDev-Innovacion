"""Pruebas del motor de coincidencias y de la puntuación de compatibilidad."""

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.models import Dimensiones, EstadoMaterial, TipoOferta, UnidadMedida
from app.services.coincidencia.puntuacion_compatibilidad_service import (
    PuntuacionCompatibilidadService,
    puntuar_distancia,
    puntuar_estado,
)


def _empresa(lat: float | None, lon: float | None) -> SimpleNamespace:
    return SimpleNamespace(
        ubicacion=SimpleNamespace(coordenadas=(lat, lon) if lat is not None else None)
    )


def _material(**datos) -> SimpleNamespace:
    base = dict(
        categoria_id=1,
        cantidad=Decimal("20"),
        unidad_medida=UnidadMedida.UNIDAD,
        estado=EstadoMaterial.BUENO,
        tipo_oferta=TipoOferta.VENTA,
        precio=Decimal("1000"),
        dimensiones=Dimensiones(100, 50, 2),
        empresa=_empresa(4.65, -74.05),
    )
    return SimpleNamespace(**{**base, **datos})


def _necesidad(**datos) -> SimpleNamespace:
    base = dict(
        categoria_id=1,
        cantidad=Decimal("10"),
        unidad_medida=UnidadMedida.UNIDAD,
        estado_minimo=EstadoMaterial.REGULAR,
        presupuesto_maximo=Decimal("50000"),
        dimensiones_minimas=Dimensiones(),
        empresa=_empresa(4.65, -74.05),
    )
    return SimpleNamespace(**{**base, **datos})


def test_compatibilidad_perfecta_vale_100() -> None:
    puntuacion = PuntuacionCompatibilidadService().calcular(_material(), _necesidad())

    assert puntuacion.total == 100
    assert puntuacion.distancia_km == 0


def test_otra_categoria_vale_0() -> None:
    puntuacion = PuntuacionCompatibilidadService().calcular(_material(categoria_id=2), _necesidad())

    assert puntuacion.total == 0


@pytest.mark.parametrize(
    ("cambios_material", "cambios_necesidad", "criterio", "esperado"),
    [
        ({"cantidad": Decimal("5")}, {}, "cantidad", 0.5),
        ({"unidad_medida": UnidadMedida.KILOGRAMO}, {}, "cantidad", 0.5),
        ({"estado": EstadoMaterial.DETERIORADO}, {}, "estado", 0.6),
        ({"precio": Decimal("10000")}, {}, "precio", 0.5),
        ({}, {"presupuesto_maximo": None}, "precio", 1.0),
        ({"tipo_oferta": TipoOferta.APROVECHAMIENTO}, {}, "precio", 1.0),
        ({}, {"dimensiones_minimas": Dimensiones(largo_cm=200, ancho_cm=10)}, "dimensiones", 0.5),
        (
            {"dimensiones": Dimensiones()},
            {"dimensiones_minimas": Dimensiones(largo_cm=10)},
            "dimensiones",
            0.5,
        ),
        ({"empresa": _empresa(None, None)}, {}, "ubicacion", 0.5),
    ],
)
def test_criterios(cambios_material, cambios_necesidad, criterio, esperado) -> None:
    puntuacion = PuntuacionCompatibilidadService().calcular(
        _material(**cambios_material), _necesidad(**cambios_necesidad)
    )

    assert getattr(puntuacion, criterio) == pytest.approx(esperado)
    if esperado < 1:
        assert puntuacion.total < 100


def test_funciones_de_distancia_y_estado() -> None:
    assert puntuar_distancia(1) == 1
    assert puntuar_distancia(500) == 0
    assert 0 < puntuar_distancia(100) < 1
    assert puntuar_estado(EstadoMaterial.NUEVO, EstadoMaterial.BUENO) == 1
    assert puntuar_estado(EstadoMaterial.REGULAR, EstadoMaterial.BUENO) == pytest.approx(0.6)


# ------------------------------------------------------------------ integración (API)


def test_publicar_necesidad_crea_coincidencias(
    client: TestClient, crear_empresa, publicar_material, publicar_necesidad
) -> None:
    ofertante = crear_empresa("oferta@x.co")
    material = publicar_material(ofertante)
    publicar_material(ofertante, categoria="tela", titulo="Lona")
    demandante = crear_empresa("demanda@x.co", latitud=4.70, longitud=-74.10)

    necesidad = publicar_necesidad(demandante)
    de_necesidad = client.get(
        f"/coincidencias/necesidades/{necesidad['id']}", headers=demandante
    ).json()
    del_ofertante = client.get("/coincidencias", headers=ofertante).json()

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
        f"/coincidencias/materiales/{material['id']}", headers=ofertante
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

    antes = client.get(f"/coincidencias/necesidades/{necesidad['id']}", headers=empresa).json()
    client.delete(f"/materiales/{material['id']}", headers=otra)
    despues = client.get(f"/coincidencias/necesidades/{necesidad['id']}", headers=empresa).json()

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
        f"/necesidades/{necesidad['id']}/estado", headers=demandante, json={"estado": "CERRADA"}
    )
    cerrada = client.get("/coincidencias", headers=ofertante).json()
    client.patch(
        f"/necesidades/{necesidad['id']}/estado", headers=demandante, json={"estado": "ABIERTA"}
    )
    recalculadas = client.post(
        f"/coincidencias/necesidades/{necesidad['id']}/recalcular", headers=demandante
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
        f"/coincidencias/necesidades/{necesidad['id']}", headers=demandante
    ).json()
    intruso = crear_empresa("intruso@x.co")

    respuesta = client.get(f"/coincidencias/{coincidencia['elementos'][0]['id']}", headers=intruso)
    ajena = client.get(f"/coincidencias/necesidades/{necesidad['id']}", headers=intruso)

    assert respuesta.status_code == 403
    assert ajena.status_code == 403
