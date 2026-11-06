"""Almacenamiento de archivos: guarda y elimina las fotos subidas.

Los archivos se guardan en la carpeta de uploads (DIRECTORIO_UPLOADS) con un nombre
aleatorio; en la base de datos solo se guarda la ruta relativa.
"""

import logging
from pathlib import Path
from uuid import uuid4

from app.core.config import settings
from app.exceptions import ArchivoInvalidoError

logger = logging.getLogger(__name__)


class AlmacenamientoArchivoService:
    def __init__(self, raiz: Path | None = None) -> None:
        self.raiz = (raiz or settings.ruta_uploads).resolve()

    def _ruta_absoluta(self, ruta_relativa: str) -> Path:
        ruta = (self.raiz / ruta_relativa).resolve()
        if not ruta.is_relative_to(self.raiz):
            raise ArchivoInvalidoError("Ruta de archivo no válida.")
        return ruta

    def guardar(self, contenido: bytes, extension: str, subcarpeta: str) -> str:
        """Guarda el contenido y devuelve la ruta relativa (p. ej. ``materiales/ab12.jpg``)."""
        ruta_relativa = f"{subcarpeta}/{uuid4().hex}{extension}"
        destino = self._ruta_absoluta(ruta_relativa)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(contenido)
        return ruta_relativa

    def leer(self, ruta_relativa: str) -> bytes:
        return self._ruta_absoluta(ruta_relativa).read_bytes()

    def copiar(self, ruta_relativa: str, subcarpeta: str) -> str:
        """Copia un archivo ya guardado a otra subcarpeta y devuelve la ruta nueva."""
        origen = self._ruta_absoluta(ruta_relativa)
        return self.guardar(origen.read_bytes(), origen.suffix, subcarpeta)

    def eliminar(self, ruta_relativa: str) -> None:
        try:
            self._ruta_absoluta(ruta_relativa).unlink(missing_ok=True)
        except OSError:
            logger.warning("No se pudo eliminar el archivo %s", ruta_relativa)
