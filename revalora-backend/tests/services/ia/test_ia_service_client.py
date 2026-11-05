"""Pruebas del cliente HTTP del servicio de IA (sin red: usa un transporte simulado)."""

import json

import httpx
import pytest

from app.exceptions import IaServiceError
from app.services.ia.ia_service_client import IaServiceClient


def _cliente(manejador) -> IaServiceClient:
    return IaServiceClient("http://ia.local", 1.0, transport=httpx.MockTransport(manejador))


def test_reconocimiento_envia_la_imagen_y_valida_la_respuesta() -> None:
    peticiones: list[httpx.Request] = []

    def manejador(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(200, json={"material": "tela", "confianza": 0.8})

    respuesta = _cliente(manejador).reconocer_material(b"datos", "foto.jpg", "image/jpeg")

    assert respuesta.material == "tela"
    assert respuesta.predicciones == []
    assert str(peticiones[0].url) == "http://ia.local/api/v1/reconocimiento"
    assert b'name="imagen"' in peticiones[0].read()


def test_recomendacion_y_oportunidades_envian_json() -> None:
    cuerpos: list[dict] = []

    def manejador(request: httpx.Request) -> httpx.Response:
        cuerpos.append(json.loads(request.content))
        if request.url.path.endswith("/recomendacion"):
            return httpx.Response(
                200, json={"producto": "mesa", "materiales": [{"material": "madera"}]}
            )
        return httpx.Response(200, json={"productos": [{"nombre": "Banco"}]})

    cliente = _cliente(manejador)

    assert cliente.recomendar_materiales("una mesa").materiales[0].material == "madera"
    assert cliente.sugerir_oportunidades(["madera"], 3).productos[0].nombre == "Banco"
    assert cuerpos == [{"descripcion": "una mesa"}, {"materiales": ["madera"], "max_productos": 3}]


@pytest.mark.parametrize(
    ("manejador", "mensaje"),
    [
        (lambda r: httpx.Response(500), "devolvió un error"),
        (
            lambda r: httpx.Response(200, json={"materiales": "no es una lista"}),
            "respuesta inválida",
        ),
        (lambda r: httpx.Response(200, content=b"no es json"), "respuesta inválida"),
    ],
)
def test_errores_se_convierten_en_ia_service_error(manejador, mensaje) -> None:
    with pytest.raises(IaServiceError, match=mensaje):
        _cliente(manejador).recomendar_materiales("x")


def test_sin_conexion_y_timeout() -> None:
    def sin_conexion(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("rechazada", request=request)

    def lento(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento", request=request)

    with pytest.raises(IaServiceError, match="conectar"):
        _cliente(sin_conexion).recomendar_materiales("x")
    with pytest.raises(IaServiceError, match="a tiempo"):
        _cliente(lento).recomendar_materiales("x")
