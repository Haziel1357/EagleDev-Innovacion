"""Pruebas unitarias de la puntuación de compatibilidad entre material y necesidad."""

from decimal import Decimal
from types import SimpleNamespace

import pytest

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
