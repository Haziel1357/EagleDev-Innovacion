"""Lógica de negocio de necesidades de materiales."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError
from app.models import Dimensiones, Empresa, EstadoNecesidad, NecesidadMaterial, OrigenCoincidencia
from app.repositories.necesidad.necesidad_material_repository import NecesidadMaterialRepository
from app.schemas.necesidad_schema import NecesidadMaterialRequest
from app.services.coincidencia.motor_coincidencia_service import MotorCoincidenciaService
from app.services.material.categoria_material_service import CategoriaMaterialService


class NecesidadMaterialService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.necesidades = NecesidadMaterialRepository(db)
        self.categorias = CategoriaMaterialService(db)
        self.motor = MotorCoincidenciaService(db)

    def buscar(
        self,
        *,
        texto: str | None,
        categoria_id: int | None,
        estado: EstadoNecesidad | None,
        empresa_id: int | None = None,
        offset: int,
        limite: int,
    ) -> tuple[Sequence[NecesidadMaterial], int]:
        return self.necesidades.buscar(
            texto=texto,
            categoria_id=categoria_id,
            estado=estado,
            empresa_id=empresa_id,
            offset=offset,
            limite=limite,
        )

    def obtener(self, necesidad_id: int) -> NecesidadMaterial:
        necesidad = self.necesidades.obtener(necesidad_id)
        if necesidad is None:
            raise RecursoNoEncontradoError("Necesidad no encontrada.")
        return necesidad

    def obtener_propia(self, empresa: Empresa, necesidad_id: int) -> NecesidadMaterial:
        necesidad = self.obtener(necesidad_id)
        if necesidad.empresa_id != empresa.id:
            raise AccesoDenegadoError("Esta necesidad no pertenece a tu empresa.")
        return necesidad

    def publicar(self, empresa: Empresa, datos: NecesidadMaterialRequest) -> NecesidadMaterial:
        self.categorias.obtener_activa(datos.categoria_id)
        necesidad = NecesidadMaterial(
            empresa=empresa, estado=EstadoNecesidad.ABIERTA, **self._campos(datos)
        )
        self.necesidades.agregar(necesidad)
        self.motor.sincronizar_necesidad(necesidad, OrigenCoincidencia.PUBLICACION_NECESIDAD)
        self.db.commit()
        return necesidad

    def actualizar(
        self, empresa: Empresa, necesidad_id: int, datos: NecesidadMaterialRequest
    ) -> NecesidadMaterial:
        necesidad = self.obtener_propia(empresa, necesidad_id)
        if datos.categoria_id != necesidad.categoria_id:
            self.categorias.obtener_activa(datos.categoria_id)
        for campo, valor in self._campos(datos).items():
            setattr(necesidad, campo, valor)
        self.motor.sincronizar_necesidad(necesidad, OrigenCoincidencia.PUBLICACION_NECESIDAD)
        self.db.commit()
        # Recarga las relaciones: si cambió categoria_id, `categoria` seguía apuntando a la anterior.
        self.db.refresh(necesidad)
        return necesidad

    def cambiar_estado(
        self, empresa: Empresa, necesidad_id: int, estado: EstadoNecesidad
    ) -> NecesidadMaterial:
        necesidad = self.obtener_propia(empresa, necesidad_id)
        necesidad.estado = estado
        self.motor.sincronizar_necesidad(necesidad, OrigenCoincidencia.PUBLICACION_NECESIDAD)
        self.db.commit()
        return necesidad

    @staticmethod
    def _campos(datos: NecesidadMaterialRequest) -> dict:
        campos = datos.model_dump(exclude={"dimensiones_minimas"})
        minimas = datos.dimensiones_minimas.model_dump() if datos.dimensiones_minimas else {}
        campos["dimensiones_minimas"] = Dimensiones(
            minimas.get("largo_cm"), minimas.get("ancho_cm"), minimas.get("alto_cm")
        )
        return campos
