"""Pruebas con el modelo CLIP real.

Se omiten si el modelo no está descargado. Para ejecutarlas:
    uv run python -m app.ml.vision.descargar_modelo
    uv run pytest -m modelo

``test_clip_reconoce_fotos_reales`` clasifica las fotos de tests/imagenes/ (ver el
README.md de esa carpeta). Si está vacía, se omite.
"""

from pathlib import Path

import pytest
from PIL import Image

from app.core.config import settings
from app.ml.materiales import CODIGOS_MATERIAL
from app.ml.vision.preprocesamiento import cargar_imagen

pytestmark = pytest.mark.modelo

CARPETA_MODELO = settings.ruta_modelos / ("models--" + settings.clip_modelo.replace("/", "--"))
CARPETA_FOTOS = Path(__file__).with_name("imagenes")
FOTOS = sorted(
    f for f in CARPETA_FOTOS.glob("*") if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)


@pytest.fixture(scope="module")
def clip():
    if not CARPETA_MODELO.exists():
        pytest.skip("Modelo CLIP no descargado (uv run python -m app.ml.vision.descargar_modelo)")
    from app.ml.vision.clasificador_materiales import ClasificadorClip

    return ClasificadorClip(settings.clip_modelo, str(settings.ruta_modelos))


def test_clip_devuelve_una_distribucion_valida(clip) -> None:
    predicciones = clip.clasificar(Image.new("RGB", (224, 224), (200, 200, 200)))

    assert {p.material for p in predicciones} == CODIGOS_MATERIAL
    assert sum(p.confianza for p in predicciones) == pytest.approx(1, abs=1e-4)
    assert predicciones == sorted(predicciones, key=lambda p: -p.confianza)


@pytest.mark.skipif(not FOTOS, reason="No hay fotos en tests/imagenes/")
@pytest.mark.parametrize("foto", FOTOS, ids=[f.name for f in FOTOS])
def test_clip_reconoce_fotos_reales(clip, foto: Path) -> None:
    esperado = foto.stem.split("_")[0]
    assert esperado in CODIGOS_MATERIAL, f"Nombre inválido: {foto.name} (usa <material>_<n>)"

    predicciones = clip.clasificar(cargar_imagen(foto.read_bytes()))

    assert predicciones[0].material == esperado, predicciones[:3]
