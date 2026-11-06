"""Preparación de las fotos antes de clasificarlas."""

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errores import ImagenInvalidaError

# Lado máximo con el que se trabaja. CLIP usa 224 px; se deja margen para su recorte central.
LADO_MAXIMO = 512

# Evita "bombas de descompresión": imágenes pequeñas en bytes pero gigantes en píxeles.
Image.MAX_IMAGE_PIXELS = 40_000_000


def cargar_imagen(contenido: bytes) -> Image.Image:
    """Abre la imagen, corrige la orientación de la cámara (EXIF), la pasa a RGB y la reduce."""
    try:
        with Image.open(io.BytesIO(contenido)) as original:
            original.load()
            imagen = ImageOps.exif_transpose(original).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, ValueError) as exc:
        raise ImagenInvalidaError("No se pudo leer la imagen; el archivo está dañado.") from exc

    if min(imagen.size) < 8:
        raise ImagenInvalidaError("La imagen es demasiado pequeña para analizarla.")
    imagen.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
    return imagen
