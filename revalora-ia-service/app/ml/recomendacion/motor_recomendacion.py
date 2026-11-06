"""Motor de recomendación sobre el catálogo de productos.

- ``recomendar``: materiales necesarios para fabricar el producto descrito.
- ``sugerir``: productos que se pueden fabricar con los materiales disponibles.
"""

from dataclasses import dataclass, field

from app.ml.materiales import CODIGOS_MATERIAL
from app.ml.recomendacion.analizador_producto import AnalizadorProducto
from app.ml.recomendacion.catalogo import Catalogo

FUNCION_MENCIONADO = "indicado en la descripción"

# Peso de cada material al calcular la viabilidad: los principales cuentan el triple,
# porque sin ellos el producto no se puede fabricar.
PESO_PRINCIPAL = 3
PESO_SECUNDARIO = 1


@dataclass(frozen=True)
class MaterialNecesario:
    material: str
    funcion: str
    cantidad_estimada: float | None = None
    unidad: str | None = None


@dataclass(frozen=True)
class Recomendacion:
    producto: str | None
    materiales: list[MaterialNecesario]


@dataclass(frozen=True)
class MaterialFaltante:
    material: str
    descripcion: str


@dataclass(frozen=True)
class ProductoViable:
    nombre: str
    descripcion: str
    viabilidad: float
    materiales_utilizados: list[str] = field(default_factory=list)
    materiales_faltantes: list[MaterialFaltante] = field(default_factory=list)


class MotorRecomendacion:
    def __init__(self, catalogo: Catalogo) -> None:
        self._catalogo = catalogo
        self._analizador = AnalizadorProducto(catalogo)

    def recomendar(self, descripcion: str) -> Recomendacion:
        """Materiales para el producto descrito.

        Si se reconoce un producto del catálogo se devuelven sus materiales (primero los
        principales) y se añaden los que el usuario mencione y el producto no incluya.
        Si no se reconoce, se devuelven solo los materiales mencionados (puede ser vacío).
        """
        analisis = self._analizador.analizar(descripcion)
        materiales: list[MaterialNecesario] = []
        if analisis.producto is not None:
            ordenados = sorted(analisis.producto.materiales, key=lambda m: not m.principal)
            materiales = [
                MaterialNecesario(m.material, m.funcion, m.cantidad_estimada, m.unidad)
                for m in ordenados
            ]
        incluidos = {m.material for m in materiales}
        materiales += [
            MaterialNecesario(codigo, FUNCION_MENCIONADO)
            for codigo in analisis.materiales_mencionados
            if codigo not in incluidos
        ]
        nombre = analisis.producto.nombre if analisis.producto else None
        return Recomendacion(producto=nombre, materiales=materiales)

    def sugerir(self, materiales: list[str], max_productos: int) -> list[ProductoViable]:
        """Productos que usan al menos uno de los materiales, del más al menos viable.

        viabilidad = peso de los materiales disponibles / peso de todos los materiales del
        producto (principal = 3, secundario = 1). Un producto con todos sus materiales
        disponibles tiene viabilidad 1.
        """
        disponibles = {m.strip().lower() for m in materiales} & CODIGOS_MATERIAL
        sugerencias: list[ProductoViable] = []
        for producto in self._catalogo.productos:
            pesos: dict[str, int] = {}
            funciones: dict[str, str] = {}
            for m in producto.materiales:
                peso = PESO_PRINCIPAL if m.principal else PESO_SECUNDARIO
                pesos[m.material] = max(pesos.get(m.material, 0), peso)
                funciones.setdefault(m.material, m.funcion)

            utilizados = [c for c in producto.codigos_material if c in disponibles]
            if not utilizados:
                continue
            viabilidad = sum(pesos[c] for c in utilizados) / sum(pesos.values())
            sugerencias.append(
                ProductoViable(
                    nombre=producto.nombre,
                    descripcion=producto.descripcion,
                    viabilidad=round(viabilidad, 2),
                    materiales_utilizados=utilizados,
                    materiales_faltantes=[
                        MaterialFaltante(c, funciones[c])
                        for c in producto.codigos_material
                        if c not in disponibles
                    ],
                )
            )
        sugerencias.sort(key=lambda p: (-p.viabilidad, -len(p.materiales_utilizados), p.nombre))
        return sugerencias[:max_productos]
