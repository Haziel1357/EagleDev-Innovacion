"""Productos que se pueden fabricar con los materiales disponibles."""

from app.ml.recomendacion.motor_recomendacion import MotorRecomendacion
from app.schemas.oportunidad_schema import (
    MaterialFaltante,
    OportunidadesResponse,
    ProductoSugerido,
)


class OportunidadService:
    def __init__(self, motor: MotorRecomendacion) -> None:
        self.motor = motor

    def sugerir(self, materiales: list[str], max_productos: int) -> OportunidadesResponse:
        productos = self.motor.sugerir(materiales, max_productos)
        return OportunidadesResponse(
            productos=[
                ProductoSugerido(
                    nombre=p.nombre,
                    descripcion=p.descripcion,
                    viabilidad=p.viabilidad,
                    materiales_utilizados=p.materiales_utilizados,
                    materiales_faltantes=[
                        MaterialFaltante(material=f.material, descripcion=f.descripcion)
                        for f in p.materiales_faltantes
                    ],
                )
                for p in productos
            ]
        )
