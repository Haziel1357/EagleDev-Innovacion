"""Validación de archivos subidos (extensión, tipo MIME y tamaño)."""

from app.core.config import settings
from app.exceptions import ArchivoInvalidoError
from app.utils.constantes import TIPOS_IMAGEN_PERMITIDOS

# Primeros bytes de cada formato: evitan aceptar un archivo que solo dice ser una imagen.
_FIRMAS = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
}


def _coincide_firma(contenido: bytes, tipo_mime: str) -> bool:
    if tipo_mime == "image/webp":
        return contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP"
    return any(contenido.startswith(firma) for firma in _FIRMAS.get(tipo_mime, ()))


def validar_imagen(contenido: bytes, tipo_mime: str | None) -> str:
    """Comprueba que el archivo sea una imagen permitida y devuelve la extensión con que guardarlo.

    Lanza ArchivoInvalidoError si está vacío, supera el tamaño máximo, el tipo no está
    permitido o el contenido no corresponde al tipo declarado.
    """
    if not contenido:
        raise ArchivoInvalidoError("El archivo está vacío.")

    maximo = settings.tamano_maximo_archivo_mb * 1024 * 1024
    if len(contenido) > maximo:
        raise ArchivoInvalidoError(
            f"El archivo supera el tamaño máximo de {settings.tamano_maximo_archivo_mb} MB."
        )

    tipo = (tipo_mime or "").lower()
    if tipo not in TIPOS_IMAGEN_PERMITIDOS:
        permitidos = ", ".join(sorted(TIPOS_IMAGEN_PERMITIDOS))
        raise ArchivoInvalidoError(f"Tipo de archivo no permitido. Usa: {permitidos}.")

    if not _coincide_firma(contenido, tipo):
        raise ArchivoInvalidoError("El contenido del archivo no corresponde a una imagen válida.")

    return TIPOS_IMAGEN_PERMITIDOS[tipo]
