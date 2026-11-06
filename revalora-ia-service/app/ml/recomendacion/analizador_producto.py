"""Interpreta una descripción en lenguaje natural ("Quiero fabricar marcos para cuadros").

Detecta dos cosas:
- el producto del catálogo que mejor encaja con la descripción, y
- los materiales que el usuario menciona explícitamente ("...con botellas de vidrio").

Funciona con palabras clave normalizadas (sin tildes, en singular), no con un modelo
entrenado: es predecible y se amplía editando catalogo_productos.json.
"""

from dataclasses import dataclass, field

from app.ml.materiales import MATERIALES
from app.ml.recomendacion.catalogo import Catalogo, ProductoCatalogo
from app.utils.texto_utils import clave, contiene, vocabulario


@dataclass(frozen=True)
class AnalisisProducto:
    producto: ProductoCatalogo | None
    # Códigos de material mencionados en la descripción, en el orden de MATERIALES.
    materiales_mencionados: list[str] = field(default_factory=list)


class AnalizadorProducto:
    def __init__(self, catalogo: Catalogo) -> None:
        self._productos = [(p, p.claves) for p in catalogo.productos]
        self._sinonimos = [
            (m.codigo, clave(s)) for m in MATERIALES for s in (m.nombre, *m.sinonimos) if clave(s)
        ]

    def analizar(self, descripcion: str) -> AnalisisProducto:
        vocab = vocabulario(descripcion)
        return AnalisisProducto(
            producto=self._mejor_producto(vocab),
            materiales_mencionados=self._materiales_mencionados(vocab),
        )

    def _mejor_producto(self, vocab: set[str]) -> ProductoCatalogo | None:
        """Producto con más palabras clave presentes. Una frase clave de varias palabras
        pesa más que una palabra suelta; en empate gana el primero del catálogo."""
        mejor, mejor_puntaje = None, 0
        for producto, claves in self._productos:
            puntaje = sum(len(k) for k in claves if contiene(vocab, k))
            if puntaje > mejor_puntaje:
                mejor, mejor_puntaje = producto, puntaje
        return mejor

    def _materiales_mencionados(self, vocab: set[str]) -> list[str]:
        coincidencias = [(codigo, k) for codigo, k in self._sinonimos if contiene(vocab, k)]
        # "botellas de vidrio" activa "botella" (plástico) y "botella vidrio" (vidrio):
        # se descarta la coincidencia contenida en otra más específica de otro material.
        validas = {
            codigo
            for codigo, k in coincidencias
            if not any(k < otra and codigo != otro for otro, otra in coincidencias)
        }
        return [m.codigo for m in MATERIALES if m.codigo in validas]
