"""Fixtures compartidas.

Las pruebas usan el clasificador heurístico (o uno falso) para no cargar CLIP, que tarda
y pesa ~600 MB. Las pruebas con el modelo real están en test_clip.py (marca ``modelo``).
"""

import io
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api.dependencias import obtener_clasificador
from app.core.config import Settings
from app.main import crear_app
from app.ml.materiales import MATERIALES
from app.ml.vision.clasificador_materiales import Prediccion

URL = "/api/v1"


class ClasificadorFalso:
    """Devuelve siempre las mismas predicciones. Guarda las imágenes que recibe."""

    nombre = "falso"

    def __init__(self) -> None:
        self.imagenes: list[Image.Image] = []
        otros = [m.codigo for m in MATERIALES if m.codigo not in ("madera", "carton")]
        self.predicciones = [
            Prediccion("madera", 0.912345),
            Prediccion("carton", 0.05),
            *(Prediccion(codigo, 0.038 / len(otros)) for codigo in otros),
        ]

    def clasificar(self, imagen: Image.Image) -> list[Prediccion]:
        self.imagenes.append(imagen)
        return self.predicciones


@pytest.fixture
def config() -> Settings:
    return Settings(modelo_vision="heuristico", cargar_modelo_al_iniciar=True, debug=False)


@pytest.fixture
def client(config: Settings) -> Iterator[TestClient]:
    with TestClient(crear_app(config)) as cliente:
        yield cliente


@pytest.fixture
def clasificador_falso(client: TestClient) -> ClasificadorFalso:
    falso = ClasificadorFalso()
    client.app.dependency_overrides[obtener_clasificador] = lambda: falso
    return falso


@pytest.fixture
def imagen() -> Callable[..., bytes]:
    """Genera una imagen en memoria: imagen(color, formato="PNG", tamano=(64, 64))."""

    def _crear(
        color: tuple[int, int, int] = (150, 100, 50),
        formato: str = "PNG",
        tamano: tuple[int, int] = (64, 64),
    ) -> bytes:
        salida = io.BytesIO()
        Image.new("RGB", tamano, color).save(salida, format=formato)
        return salida.getvalue()

    return _crear
