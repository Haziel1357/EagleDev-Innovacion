"""Motor de coincidencias: cruza ofertas de materiales con necesidades.

Se ejecuta al publicar o modificar un material o una necesidad, y también cuando el
usuario pide recalcular. Guarda solo los cruces con puntuación >= UMBRAL_COINCIDENCIA
y borra los que dejaron de ser compatibles.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError
from app.models import (
    Coincidencia,
    Empresa,
    EstadoNecesidad,
    MaterialSobrante,
    NecesidadMaterial,
    OrigenCoincidencia,
)
from app.repositories.coincidencia.coincidencia_repository import CoincidenciaRepository
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.repositories.necesidad.necesidad_material_repository import NecesidadMaterialRepository
from app.services.coincidencia.puntuacion_compatibilidad_service import (
    PuntuacionCompatibilidadService,
)
from app.utils.constantes import UMBRAL_COINCIDENCIA


class MotorCoincidenciaService:
    def __init__(self, db: Session, umbral: float = UMBRAL_COINCIDENCIA) -> None:
        self.db = db
        self.umbral = umbral
        self.coincidencias = CoincidenciaRepository(db)
        self.materiales = MaterialSobranteRepository(db)
        self.necesidades = NecesidadMaterialRepository(db)
        self.puntuacion = PuntuacionCompatibilidadService()

    # ------------------------------------------------------------------ sincronización

    def sincronizar_material(
        self, material: MaterialSobrante, origen: OrigenCoincidencia
    ) -> list[Coincidencia]:
        """Recalcula las coincidencias de un material (sin confirmar la transacción)."""
        if not material.esta_disponible:
            self.coincidencias.eliminar_de_material(material.id, excepto=set())
            return []
        necesidades = self.necesidades.abiertas_por_categoria(
            material.categoria_id, excluir_empresa_id=material.empresa_id
        )
        resultado = [c for n in necesidades if (c := self._guardar(material, n, origen))]
        self.coincidencias.eliminar_de_material(
            material.id, excepto={c.necesidad_id for c in resultado}
        )
        self.db.flush()
        return sorted(resultado, key=lambda c: c.puntuacion, reverse=True)

    def sincronizar_necesidad(
        self, necesidad: NecesidadMaterial, origen: OrigenCoincidencia
    ) -> list[Coincidencia]:
        """Recalcula las coincidencias de una necesidad (sin confirmar la transacción)."""
        if necesidad.estado != EstadoNecesidad.ABIERTA:
            self.coincidencias.eliminar_de_necesidad(necesidad.id, excepto=set())
            return []
        materiales = self.materiales.disponibles_por_categoria(
            necesidad.categoria_id, excluir_empresa_id=necesidad.empresa_id
        )
        resultado = [c for m in materiales if (c := self._guardar(m, necesidad, origen))]
        self.coincidencias.eliminar_de_necesidad(
            necesidad.id, excepto={c.material_id for c in resultado}
        )
        self.db.flush()
        return sorted(resultado, key=lambda c: c.puntuacion, reverse=True)

    def _guardar(
        self, material: MaterialSobrante, necesidad: NecesidadMaterial, origen: OrigenCoincidencia
    ) -> Coincidencia | None:
        puntuacion = self.puntuacion.calcular(material, necesidad)
        if puntuacion.total < self.umbral:
            return None
        detalle = puntuacion.model_dump(exclude={"total", "distancia_km"})
        coincidencia = self.coincidencias.por_par(material.id, necesidad.id)
        if coincidencia is None:
            coincidencia = Coincidencia(material=material, necesidad=necesidad)
            self.db.add(coincidencia)
        coincidencia.puntuacion = puntuacion.total
        coincidencia.detalle = detalle
        coincidencia.distancia_km = puntuacion.distancia_km
        coincidencia.origen = origen
        return coincidencia

    # ------------------------------------------------------------- casos de uso (API)

    def recalcular_para_material(self, empresa: Empresa, material_id: int) -> list[Coincidencia]:
        material = self._material_propio(empresa, material_id)
        resultado = self.sincronizar_material(material, OrigenCoincidencia.MANUAL)
        self.db.commit()
        return resultado

    def recalcular_para_necesidad(self, empresa: Empresa, necesidad_id: int) -> list[Coincidencia]:
        necesidad = self._necesidad_propia(empresa, necesidad_id)
        resultado = self.sincronizar_necesidad(necesidad, OrigenCoincidencia.MANUAL)
        self.db.commit()
        return resultado

    def de_material(
        self, empresa: Empresa, material_id: int, offset: int, limite: int
    ) -> tuple[Sequence[Coincidencia], int]:
        self._material_propio(empresa, material_id)
        return self.coincidencias.de_material(material_id, offset, limite)

    def de_necesidad(
        self, empresa: Empresa, necesidad_id: int, offset: int, limite: int
    ) -> tuple[Sequence[Coincidencia], int]:
        self._necesidad_propia(empresa, necesidad_id)
        return self.coincidencias.de_necesidad(necesidad_id, offset, limite)

    def de_empresa(
        self, empresa: Empresa, offset: int, limite: int
    ) -> tuple[Sequence[Coincidencia], int]:
        return self.coincidencias.de_empresa(empresa.id, offset, limite)

    def obtener(self, empresa: Empresa, coincidencia_id: int) -> Coincidencia:
        coincidencia = self.coincidencias.obtener(coincidencia_id)
        if coincidencia is None:
            raise RecursoNoEncontradoError("Coincidencia no encontrada.")
        if empresa.id not in (coincidencia.material.empresa_id, coincidencia.necesidad.empresa_id):
            raise AccesoDenegadoError("Esta coincidencia no pertenece a tu empresa.")
        return coincidencia

    def _material_propio(self, empresa: Empresa, material_id: int) -> MaterialSobrante:
        material = self.materiales.obtener(material_id)
        if material is None:
            raise RecursoNoEncontradoError("Material no encontrado.")
        if material.empresa_id != empresa.id:
            raise AccesoDenegadoError("Este material no pertenece a tu empresa.")
        return material

    def _necesidad_propia(self, empresa: Empresa, necesidad_id: int) -> NecesidadMaterial:
        necesidad = self.necesidades.obtener(necesidad_id)
        if necesidad is None:
            raise RecursoNoEncontradoError("Necesidad no encontrada.")
        if necesidad.empresa_id != empresa.id:
            raise AccesoDenegadoError("Esta necesidad no pertenece a tu empresa.")
        return necesidad
