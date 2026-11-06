"""Descarga el modelo CLIP en modelos_entrenados/ (unos 600 MB, una sola vez).

Uso:
    uv run python -m app.ml.vision.descargar_modelo

No es obligatorio: el servicio lo descarga solo al arrancar si no está. Hacerlo antes evita
que el primer arranque tarde varios minutos.
"""

from app.core.config import settings
from app.core.logging import configurar_logging
from app.ml.vision.clasificador_materiales import ClasificadorClip


def main() -> None:
    configurar_logging(debug=False)
    settings.ruta_modelos.mkdir(parents=True, exist_ok=True)
    ClasificadorClip(settings.clip_modelo, str(settings.ruta_modelos))
    print(f"Modelo {settings.clip_modelo} listo en {settings.ruta_modelos}")


if __name__ == "__main__":
    main()
