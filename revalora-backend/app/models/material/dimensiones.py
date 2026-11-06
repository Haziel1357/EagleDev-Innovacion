"""Dimensiones: medidas de un material sobrante (en centímetros).

Es un valor embebido (no tiene tabla propia): se guarda en tres columnas de la
entidad que lo usa, mediante `composite` de SQLAlchemy.
"""

from dataclasses import dataclass


@dataclass
class Dimensiones:
    largo_cm: float | None = None
    ancho_cm: float | None = None
    alto_cm: float | None = None

    def es_vacia(self) -> bool:
        return self.largo_cm is None and self.ancho_cm is None and self.alto_cm is None

    def cubre(self, minimas: "Dimensiones") -> float:
        """Proporción (0-1) de las medidas mínimas indicadas que estas dimensiones cumplen."""
        pares = [
            (propia, minima)
            for propia, minima in (
                (self.largo_cm, minimas.largo_cm),
                (self.ancho_cm, minimas.ancho_cm),
                (self.alto_cm, minimas.alto_cm),
            )
            if minima is not None
        ]
        if not pares:
            return 1.0
        cumplidas = sum(1 for propia, minima in pares if propia is not None and propia >= minima)
        return cumplidas / len(pares)
