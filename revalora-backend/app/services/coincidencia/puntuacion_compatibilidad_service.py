"""Puntuación de compatibilidad según material, dimensiones, cantidad, estado, ubicación y precio.

Cada criterio se puntúa de 0 a 1 y el total es la suma ponderada (PESOS_COMPATIBILIDAD)
expresada de 0 a 100. Si el material no es de la categoría que se necesita, el total es 0.
Cuando falta un dato para evaluar un criterio (p. ej. coordenadas), ese criterio vale 0.5.
"""

from decimal import Decimal

from app.models import EstadoMaterial, MaterialSobrante, NecesidadMaterial, TipoOferta
from app.schemas.coincidencia_schema import PuntuacionCompatibilidadResponse
from app.utils.constantes import DISTANCIA_IDEAL_KM, DISTANCIA_MAXIMA_KM, PESOS_COMPATIBILIDAD
from app.utils.geo_distancia import distancia_opcional

NEUTRO = 0.5


def puntuar_cantidad(disponible: Decimal, requerida: Decimal, misma_unidad: bool) -> float:
    if not misma_unidad or requerida <= 0:
        return NEUTRO
    return float(min(Decimal(1), disponible / requerida))


def puntuar_estado(estado: EstadoMaterial, minimo: EstadoMaterial) -> float:
    diferencia = minimo.nivel - estado.nivel
    if diferencia <= 0:
        return 1.0
    return max(0.0, 1.0 - 0.4 * diferencia)


def puntuar_distancia(distancia: float | None) -> float:
    if distancia is None:
        return NEUTRO
    if distancia <= DISTANCIA_IDEAL_KM:
        return 1.0
    if distancia >= DISTANCIA_MAXIMA_KM:
        return 0.0
    return 1.0 - (distancia - DISTANCIA_IDEAL_KM) / (DISTANCIA_MAXIMA_KM - DISTANCIA_IDEAL_KM)


def puntuar_precio(
    material: MaterialSobrante, cantidad: Decimal, presupuesto: Decimal | None
) -> float:
    """El precio del material es por unidad de medida; el presupuesto es el total disponible."""
    if material.tipo_oferta != TipoOferta.VENTA or not material.precio:
        return 1.0
    if presupuesto is None:
        return 1.0
    costo = material.precio * cantidad
    if costo <= presupuesto:
        return 1.0
    return float(presupuesto / costo) if costo > 0 else 1.0


class PuntuacionCompatibilidadService:
    def __init__(self, pesos: dict[str, float] | None = None) -> None:
        self.pesos = pesos or PESOS_COMPATIBILIDAD

    def calcular(
        self, material: MaterialSobrante, necesidad: NecesidadMaterial
    ) -> PuntuacionCompatibilidadResponse:
        distancia = distancia_opcional(
            material.empresa.ubicacion.coordenadas, necesidad.empresa.ubicacion.coordenadas
        )
        if material.categoria_id != necesidad.categoria_id:
            return PuntuacionCompatibilidadResponse(
                total=0,
                material=0,
                cantidad=0,
                estado=0,
                dimensiones=0,
                ubicacion=0,
                precio=0,
                distancia_km=self._redondear(distancia),
            )

        misma_unidad = material.unidad_medida == necesidad.unidad_medida
        cantidad_negociable = min(material.cantidad, necesidad.cantidad)

        minimas = necesidad.dimensiones_minimas
        if minimas.es_vacia():
            dimensiones = 1.0
        elif material.dimensiones.es_vacia():
            dimensiones = NEUTRO
        else:
            dimensiones = material.dimensiones.cubre(minimas)

        criterios = {
            "material": 1.0,
            "cantidad": puntuar_cantidad(material.cantidad, necesidad.cantidad, misma_unidad),
            "estado": puntuar_estado(material.estado, necesidad.estado_minimo),
            "dimensiones": dimensiones,
            "ubicacion": puntuar_distancia(distancia),
            "precio": puntuar_precio(
                material,
                cantidad_negociable if misma_unidad else material.cantidad,
                necesidad.presupuesto_maximo,
            ),
        }
        total = 100 * sum(self.pesos[nombre] * valor for nombre, valor in criterios.items())
        return PuntuacionCompatibilidadResponse(
            total=round(total, 2),
            **{nombre: round(valor, 4) for nombre, valor in criterios.items()},
            distancia_km=self._redondear(distancia),
        )

    @staticmethod
    def _redondear(valor: float | None) -> float | None:
        return round(valor, 2) if valor is not None else None
