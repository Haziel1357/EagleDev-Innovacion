"""Materiales necesarios para fabricar un producto descrito en lenguaje natural."""

from app.ml.recomendacion.motor_recomendacion import MotorRecomendacion
from app.schemas.recomendacion_schema import MaterialRecomendado, RecomendacionResponse


class RecomendacionService:
    def __init__(self, motor: MotorRecomendacion) -> None:
        self.motor = motor

    def recomendar(self, descripcion: str) -> RecomendacionResponse:
        recomendacion = self.motor.recomendar(descripcion)
        return RecomendacionResponse(
            producto=recomendacion.producto,
            materiales=[
                MaterialRecomendado(
                    material=m.material,
                    funcion=m.funcion,
                    cantidad_estimada=m.cantidad_estimada,
                    unidad=m.unidad,
                )
                for m in recomendacion.materiales
            ],
        )
