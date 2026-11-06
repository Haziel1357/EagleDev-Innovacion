"""Validación de los archivos de imagen recibidos."""

from app.core.config import settings
from app.core.errores import ImagenDemasiadoGrandeError, ImagenInvalidaError

FORMATOS_ACEPTADOS = "JPG, PNG o WEBP"


def detectar_formato(contenido: bytes) -> str | None:
    """Formato real según la firma del archivo (no se confía en la extensión ni en el MIME)."""
    if contenido.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if contenido.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP":
        return "webp"
    return None


def validar_imagen(contenido: bytes) -> str:
    """Comprueba tamaño y formato. Devuelve el formato detectado."""
    if not contenido:
        raise ImagenInvalidaError("La imagen está vacía.")
    if len(contenido) > settings.tamano_maximo_imagen_bytes:
        raise ImagenDemasiadoGrandeError(
            f"La imagen supera el máximo de {settings.tamano_maximo_imagen_mb} MB."
        )
    formato = detectar_formato(contenido)
    if formato is None:
        raise ImagenInvalidaError(f"Formato no soportado. Envía una imagen {FORMATOS_ACEPTADOS}.")
    return formato
