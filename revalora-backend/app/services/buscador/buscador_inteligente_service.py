"""Buscador inteligente: pide a la IA los materiales necesarios para fabricar un producto y prioriza los sobrantes disponibles.

Ejemplo: "Quiero fabricar marcos para cuadros" -> la IA responde madera (estructura),
vidrio (protección) y cartón (respaldo). Para cada material se buscan las publicaciones
disponibles y se ordenan por estado, cercanía, cantidad y precio.
"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError
from app.models import (
    BusquedaFabricacion,
    EstadoMaterial,
    MaterialRequerido,
    MaterialSobrante,
    TipoOferta,
    UnidadMedida,
    Usuario,
)
from app.repositories.buscador.busqueda_fabricacion_repository import BusquedaFabricacionRepository
from app.repositories.material.categoria_material_repository import CategoriaMaterialRepository
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.schemas.buscador_schema import (
    BusquedaFabricacionRequest,
    MaterialRecomendadoResponse,
    MaterialRequeridoResponse,
    ResultadoBusquedaResponse,
)
from app.schemas.ia_schema import MaterialRecomendadoIA
from app.schemas.material_schema import CategoriaMaterialResponse, MaterialSobranteResponse
from app.services.coincidencia.puntuacion_compatibilidad_service import (
    puntuar_cantidad,
    puntuar_distancia,
    puntuar_estado,
)
from app.services.ia.ia_service_client import IaServiceClient
from app.utils.geo_distancia import distancia_opcional

PESOS_BUSQUEDA = {
    "estado": 0.25,
    "ubicacion": 0.30,
    "cantidad": 0.20,
    "precio": 0.20,
    "verificado": 0.05,
}


def _unidad(valor: str | None) -> UnidadMedida | None:
    if not valor:
        return None
    try:
        return UnidadMedida(valor.strip().upper())
    except ValueError:
        return None


class BuscadorInteligenteService:
    def __init__(self, db: Session, ia: IaServiceClient) -> None:
        self.db = db
        self.ia = ia
        self.busquedas = BusquedaFabricacionRepository(db)
        self.categorias = CategoriaMaterialRepository(db)
        self.materiales = MaterialSobranteRepository(db)

    def buscar(
        self, usuario: Usuario, datos: BusquedaFabricacionRequest
    ) -> ResultadoBusquedaResponse:
        recomendacion = self.ia.recomendar_materiales(datos.descripcion)

        busqueda = BusquedaFabricacion(
            usuario_id=usuario.id,
            descripcion=datos.descripcion.strip(),
            producto_interpretado=recomendacion.producto,
            materiales_requeridos=self._materiales_requeridos(recomendacion.materiales),
        )
        self.busquedas.agregar(busqueda)
        self.db.commit()

        origen = None
        if datos.latitud is not None and datos.longitud is not None:
            origen = (datos.latitud, datos.longitud)
        elif usuario.empresa is not None:
            origen = usuario.empresa.ubicacion.coordenadas

        requeridos = []
        for requerido in busqueda.materiales_requeridos:
            resultados = []
            if requerido.categoria_id is not None:
                candidatos = self.materiales.disponibles_por_categoria(
                    requerido.categoria_id, excluir_empresa_id=usuario.empresa_id
                )
                resultados = self._priorizar(candidatos, requerido, origen)[
                    : datos.limite_por_material
                ]
            requeridos.append(self._respuesta_requerido(requerido, resultados))

        return ResultadoBusquedaResponse(
            busqueda_id=busqueda.id,
            descripcion=busqueda.descripcion,
            producto_interpretado=busqueda.producto_interpretado,
            materiales_requeridos=requeridos,
            total_resultados=sum(len(r.resultados) for r in requeridos),
            creado_en=busqueda.creado_en,
        )

    def historial(
        self, usuario: Usuario, offset: int, limite: int
    ) -> tuple[Sequence[BusquedaFabricacion], int]:
        return self.busquedas.de_usuario(usuario.id, offset, limite)

    def obtener(self, usuario: Usuario, busqueda_id: int) -> BusquedaFabricacion:
        busqueda = self.busquedas.obtener(busqueda_id)
        if busqueda is None:
            raise RecursoNoEncontradoError("Búsqueda no encontrada.")
        if busqueda.usuario_id != usuario.id and not usuario.es_admin:
            raise AccesoDenegadoError("Esta búsqueda no es tuya.")
        return busqueda

    # ------------------------------------------------------------------------ apoyo

    def _materiales_requeridos(
        self, recomendados: list[MaterialRecomendadoIA]
    ) -> list[MaterialRequerido]:
        categorias = self.categorias.por_codigos(m.material for m in recomendados)
        requeridos: list[MaterialRequerido] = []
        vistos: set[str] = set()
        for recomendado in recomendados:
            codigo = recomendado.material.strip().lower()
            if codigo in vistos:
                continue
            vistos.add(codigo)
            categoria = categorias.get(codigo)
            requeridos.append(
                MaterialRequerido(
                    material=codigo,
                    categoria=categoria,
                    funcion=recomendado.funcion,
                    cantidad_estimada=recomendado.cantidad_estimada,
                    unidad_medida=_unidad(recomendado.unidad),
                )
            )
        return requeridos

    def _priorizar(
        self,
        candidatos: Sequence[MaterialSobrante],
        requerido: MaterialRequerido,
        origen: tuple[float, float] | None,
    ) -> list[MaterialRecomendadoResponse]:
        precios = [m.precio for m in candidatos if m.tipo_oferta == TipoOferta.VENTA and m.precio]
        precio_minimo = min(precios) if precios else None

        puntuados = []
        for material in candidatos:
            distancia = distancia_opcional(origen, material.empresa.ubicacion.coordenadas)
            material.distancia_km = round(distancia, 2) if distancia is not None else None
            criterios = {
                "estado": puntuar_estado(material.estado, EstadoMaterial.NUEVO),
                "ubicacion": puntuar_distancia(distancia),
                "cantidad": self._puntuar_cantidad(material, requerido),
                "precio": self._puntuar_precio(material, precio_minimo),
                "verificado": 1.0 if material.verificado_ia else 0.0,
            }
            total = 100 * sum(PESOS_BUSQUEDA[k] * v for k, v in criterios.items())
            puntuados.append((round(total, 2), material))

        puntuados.sort(key=lambda par: (-par[0], par[1].id))
        return [
            MaterialRecomendadoResponse(
                puntuacion=puntuacion, material=MaterialSobranteResponse.model_validate(material)
            )
            for puntuacion, material in puntuados
        ]

    @staticmethod
    def _puntuar_cantidad(material: MaterialSobrante, requerido: MaterialRequerido) -> float:
        if requerido.cantidad_estimada is None:
            return 1.0
        return puntuar_cantidad(
            material.cantidad,
            requerido.cantidad_estimada,
            requerido.unidad_medida is None or requerido.unidad_medida == material.unidad_medida,
        )

    @staticmethod
    def _puntuar_precio(material: MaterialSobrante, precio_minimo: Decimal | None) -> float:
        """Gratis o por intercambio vale 1; en venta, el más barato vale 1 y el resto en proporción."""
        if material.tipo_oferta != TipoOferta.VENTA or not material.precio:
            return 1.0
        if precio_minimo is None:
            return 1.0
        return float(precio_minimo / material.precio)

    @staticmethod
    def _respuesta_requerido(
        requerido: MaterialRequerido, resultados: list[MaterialRecomendadoResponse]
    ) -> MaterialRequeridoResponse:
        return MaterialRequeridoResponse(
            material=requerido.material,
            funcion=requerido.funcion,
            categoria=(
                CategoriaMaterialResponse.model_validate(requerido.categoria)
                if requerido.categoria
                else None
            ),
            cantidad_estimada=requerido.cantidad_estimada,
            unidad_medida=requerido.unidad_medida,
            resultados=resultados,
        )
