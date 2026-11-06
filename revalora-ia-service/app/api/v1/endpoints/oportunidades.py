"""POST /api/v1/oportunidades: productos que se pueden fabricar con ciertos materiales."""

from fastapi import APIRouter

from app.api.dependencias import MotorDep
from app.schemas.oportunidad_schema import OportunidadesRequest, OportunidadesResponse
from app.services.oportunidad_service import OportunidadService

router = APIRouter(tags=["Oportunidades"])


@router.post("/oportunidades", response_model=OportunidadesResponse)
def sugerir_oportunidades(datos: OportunidadesRequest, motor: MotorDep) -> OportunidadesResponse:
    """Productos del catálogo que usan al menos uno de los materiales, ordenados por
    viabilidad (1 = se tienen todos los materiales), con los materiales que faltan."""
    return OportunidadService(motor).sugerir(datos.materiales, datos.max_productos)
