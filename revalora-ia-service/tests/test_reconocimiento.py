"""Pruebas de POST /api/v1/reconocimiento y del clasificador heurístico."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import settings
from app.ml.materiales import CODIGOS_MATERIAL
from app.ml.vision.clasificador_materiales import ClasificadorHeuristico
from tests.conftest import URL

RUTA = f"{URL}/reconocimiento"


def _enviar(client: TestClient, contenido: bytes, nombre: str = "foto.png", tipo="image/png"):
    return client.post(RUTA, files={"imagen": (nombre, contenido, tipo)})


# ------------------------------------------------------------------------- contrato


def test_respuesta_cumple_el_contrato(client: TestClient, clasificador_falso, imagen) -> None:
    respuesta = _enviar(client, imagen())

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["material"] == "madera"
    assert cuerpo["confianza"] == 0.9123
    assert cuerpo["modelo"] == "falso"
    assert [p["material"] for p in cuerpo["predicciones"]][:2] == ["madera", "carton"]
    assert len(cuerpo["predicciones"]) == settings.max_predicciones


def test_acepta_jpg_png_y_webp(client: TestClient, clasificador_falso, imagen) -> None:
    for formato, tipo in (("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")):
        respuesta = _enviar(client, imagen(formato=formato), f"foto.{formato.lower()}", tipo)
        assert respuesta.status_code == 200, (formato, respuesta.text)
    assert len(clasificador_falso.imagenes) == 3


def test_reduce_la_imagen_y_corrige_la_orientacion(client: TestClient, clasificador_falso) -> None:
    salida = io.BytesIO()
    foto = Image.new("RGB", (2000, 1000), (10, 20, 30))
    exif = foto.getexif()
    exif[0x0112] = 6  # orientación EXIF: girada 90°, como sale de muchos celulares
    foto.save(salida, format="JPEG", exif=exif)

    _enviar(client, salida.getvalue(), "foto.jpg", "image/jpeg")

    recibida = clasificador_falso.imagenes[0]
    assert recibida.mode == "RGB"
    assert recibida.size == (256, 512)  # girada (1000x2000) y reducida a 512 de lado


# ------------------------------------------------------------------------- errores


@pytest.mark.parametrize(
    ("contenido", "mensaje"),
    [
        (b"", "vacía"),
        (b"esto no es una imagen", "Formato no soportado"),
        (b"%PDF-1.7 documento", "Formato no soportado"),
        (b"\x89PNG\r\n\x1a\n" + b"datos corruptos", "dañado"),
    ],
)
def test_archivos_invalidos_responden_400(client: TestClient, contenido, mensaje) -> None:
    respuesta = _enviar(client, contenido)

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["mensaje"]


def test_imagen_demasiado_pequena(client: TestClient, imagen) -> None:
    respuesta = _enviar(client, imagen(tamano=(4, 4)))

    assert respuesta.status_code == 400
    assert "pequeña" in respuesta.json()["mensaje"]


def test_imagen_demasiado_grande_responde_413(
    client: TestClient, imagen, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "tamano_maximo_imagen_mb", 0)

    respuesta = _enviar(client, imagen())

    assert respuesta.status_code == 413


def test_sin_archivo_responde_422(client: TestClient) -> None:
    respuesta = client.post(RUTA)

    assert respuesta.status_code == 422
    assert respuesta.json()["detalles"][0]["campo"] == "body.imagen"


# ---------------------------------------------------------------- clasificador heurístico


def test_heuristico_por_http(client: TestClient, imagen) -> None:
    cuerpo = _enviar(client, imagen()).json()

    assert cuerpo["modelo"] == "heuristico"
    assert cuerpo["material"] in CODIGOS_MATERIAL
    assert 0 < cuerpo["confianza"] <= ClasificadorHeuristico.CONFIANZA_MAXIMA


@pytest.mark.parametrize(
    ("color", "esperado"),
    [
        ((240, 240, 238), "papel"),  # blanco liso
        ((230, 20, 30), "plastico"),  # rojo intenso
    ],
)
def test_heuristico_casos_claros(color, esperado) -> None:
    predicciones = ClasificadorHeuristico().clasificar(Image.new("RGB", (64, 64), color))

    assert predicciones[0].material == esperado


def test_heuristico_nunca_supera_la_confianza_maxima() -> None:
    for color in ((0, 0, 0), (255, 255, 255), (150, 100, 50), (0, 200, 0)):
        predicciones = ClasificadorHeuristico().clasificar(Image.new("RGB", (64, 64), color))

        assert {p.material for p in predicciones} == CODIGOS_MATERIAL
        assert sum(p.confianza for p in predicciones) == pytest.approx(1)
        assert predicciones[0].confianza <= ClasificadorHeuristico.CONFIANZA_MAXIMA
        assert predicciones == sorted(predicciones, key=lambda p: -p.confianza)
