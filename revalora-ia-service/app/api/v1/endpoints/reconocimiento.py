"""POST /api/v1/reconocimiento: clasifica el material de una foto."""

from typing import Annotated

from fastapi import APIRouter, File, UploadFile

from app.api.dependencias import ClasificadorDep
from app.core.config import settings
from app.schemas.reconocimiento_schema import ReconocimientoResponse
from app.services.reconocimiento_service import ReconocimientoService

router = APIRouter(tags=["Reconocimiento"])


@router.post("/reconocimiento", response_model=ReconocimientoResponse)
def reconocer_material(
    imagen: Annotated[UploadFile, File(description="Foto del material (JPG, PNG o WEBP).")],
    clasificador: ClasificadorDep,
) -> ReconocimientoResponse:
    """Clasifica el material de la foto: madera, carton, plastico, tela, metal, vidrio,
    papel u otro.

    Es una función síncrona a propósito: FastAPI la ejecuta en un hilo aparte y el
    cálculo del modelo no bloquea al resto de peticiones.
    """
    # Se lee un byte más del máximo para detectar archivos demasiado grandes sin cargarlos enteros.
    contenido = imagen.file.read(settings.tamano_maximo_imagen_bytes + 1)
    return ReconocimientoService(clasificador).reconocer(contenido)
