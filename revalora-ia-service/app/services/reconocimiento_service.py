"""Reconocimiento del material de una foto."""

from app.core.config import settings
from app.ml.vision.clasificador_materiales import ClasificadorMateriales
from app.ml.vision.preprocesamiento import cargar_imagen
from app.schemas.reconocimiento_schema import PrediccionMaterial, ReconocimientoResponse
from app.utils.imagen_utils import validar_imagen


class ReconocimientoService:
    def __init__(self, clasificador: ClasificadorMateriales) -> None:
        self.clasificador = clasificador

    def reconocer(self, contenido: bytes) -> ReconocimientoResponse:
        validar_imagen(contenido)
        imagen = cargar_imagen(contenido)
        predicciones = self.clasificador.clasificar(imagen)[: settings.max_predicciones]
        mejor = predicciones[0]
        return ReconocimientoResponse(
            material=mejor.material,
            confianza=round(mejor.confianza, 4),
            predicciones=[
                PrediccionMaterial(material=p.material, confianza=round(p.confianza, 4))
                for p in predicciones
            ],
            modelo=self.clasificador.nombre,
        )
