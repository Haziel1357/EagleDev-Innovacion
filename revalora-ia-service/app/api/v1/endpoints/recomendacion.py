"""POST /api/v1/recomendacion: materiales necesarios para fabricar un producto."""

from fastapi import APIRouter

from app.api.dependencias import MotorDep
from app.schemas.recomendacion_schema import RecomendacionRequest, RecomendacionResponse
from app.services.recomendacion_service import RecomendacionService

router = APIRouter(tags=["Recomendación"])


@router.post("/recomendacion", response_model=RecomendacionResponse)
def recomendar_materiales(datos: RecomendacionRequest, motor: MotorDep) -> RecomendacionResponse:
    """Interpreta la descripción y devuelve los materiales del producto reconocido.

    Si no se reconoce ningún producto del catálogo, `producto` es `null` y solo se
    devuelven los materiales mencionados en la descripción (puede ser una lista vacía).
    """
    return RecomendacionService(motor).recomendar(datos.descripcion)
