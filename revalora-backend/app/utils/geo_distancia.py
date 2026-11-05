"""Cálculo de distancias geográficas entre ubicaciones (fórmula de Haversine)."""

from math import asin, cos, radians, sin, sqrt

RADIO_TIERRA_KM = 6371.0088

Coordenadas = tuple[float, float]
"""(latitud, longitud) en grados decimales."""


def distancia_km(origen: Coordenadas, destino: Coordenadas) -> float:
    """Distancia en kilómetros sobre la superficie terrestre entre dos coordenadas."""
    lat1, lon1 = map(radians, origen)
    lat2, lon2 = map(radians, destino)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


def distancia_opcional(origen: Coordenadas | None, destino: Coordenadas | None) -> float | None:
    """Igual que distancia_km, pero devuelve None si falta alguna de las coordenadas."""
    if origen is None or destino is None:
        return None
    return distancia_km(origen, destino)
