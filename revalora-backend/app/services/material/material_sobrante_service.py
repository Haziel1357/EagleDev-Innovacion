"""Lógica de negocio de materiales sobrantes."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError, ReglaNegocioError
from app.models import (
    ClasificacionMaterial,
    Dimensiones,
    DisponibilidadMaterial,
    Empresa,
    EstadoVerificacion,
    MaterialSobrante,
    OrigenCoincidencia,
    Usuario,
)
from app.repositories.ia.clasificacion_material_repository import ClasificacionMaterialRepository
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.schemas.material_schema import FiltroMaterialRequest, MaterialSobranteRequest
from app.services.coincidencia.motor_coincidencia_service import MotorCoincidenciaService
from app.services.material.categoria_material_service import CategoriaMaterialService
from app.services.material.foto_material_service import FotoMaterialService


class MaterialSobranteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.materiales = MaterialSobranteRepository(db)
        self.clasificaciones = ClasificacionMaterialRepository(db)
        self.categorias = CategoriaMaterialService(db)
        self.fotos = FotoMaterialService(db)
        self.motor = MotorCoincidenciaService(db)

    # ---------------------------------------------------------------------- consultas

    def buscar(
        self,
        filtro: FiltroMaterialRequest,
        *,
        offset: int,
        limite: int,
        orden: str = "recientes",
        excluir_empresa_id: int | None = None,
    ) -> tuple[Sequence[MaterialSobrante], int]:
        return self.materiales.buscar(
            filtro, offset=offset, limite=limite, orden=orden, excluir_empresa_id=excluir_empresa_id
        )

    def de_empresa(
        self, empresa: Empresa, offset: int, limite: int
    ) -> tuple[Sequence[MaterialSobrante], int]:
        return self.materiales.de_empresa(empresa.id, offset, limite)

    def obtener(self, material_id: int, usuario: Usuario | None = None) -> MaterialSobrante:
        """Detalle público. Un material retirado solo lo ve su dueño (o un administrador)."""
        material = self.materiales.obtener(material_id)
        if material is None:
            raise RecursoNoEncontradoError("Material no encontrado.")
        if material.disponibilidad == DisponibilidadMaterial.RETIRADO and not (
            usuario and (usuario.es_admin or usuario.empresa_id == material.empresa_id)
        ):
            raise RecursoNoEncontradoError("Material no encontrado.")
        return material

    def obtener_propio(self, empresa: Empresa, material_id: int) -> MaterialSobrante:
        material = self.materiales.obtener(material_id)
        if material is None:
            raise RecursoNoEncontradoError("Material no encontrado.")
        if material.empresa_id != empresa.id:
            raise AccesoDenegadoError("Este material no pertenece a tu empresa.")
        return material

    # ------------------------------------------------------------------ modificaciones

    def publicar(
        self, usuario: Usuario, empresa: Empresa, datos: MaterialSobranteRequest
    ) -> MaterialSobrante:
        self.categorias.obtener_activa(datos.categoria_id)
        clasificacion = self._clasificacion_utilizable(usuario, datos.clasificacion_id)

        material = MaterialSobrante(
            empresa=empresa,
            disponibilidad=DisponibilidadMaterial.DISPONIBLE,
            verificado_ia=False,
            **self._campos(datos),
        )
        self.materiales.agregar(material)

        if clasificacion is not None:
            self._vincular_clasificacion(material, clasificacion)

        self.motor.sincronizar_material(material, OrigenCoincidencia.PUBLICACION_MATERIAL)
        self.db.commit()
        self.db.refresh(material)
        return material

    def actualizar(
        self, usuario: Usuario, empresa: Empresa, material_id: int, datos: MaterialSobranteRequest
    ) -> MaterialSobrante:
        material = self.obtener_propio(empresa, material_id)
        if material.disponibilidad == DisponibilidadMaterial.RETIRADO:
            raise ReglaNegocioError("No se puede modificar un material retirado.")
        cambia_categoria = datos.categoria_id != material.categoria_id
        if cambia_categoria:
            self.categorias.obtener_activa(datos.categoria_id)
        clasificacion = self._clasificacion_utilizable(usuario, datos.clasificacion_id, material.id)

        for campo, valor in self._campos(datos).items():
            setattr(material, campo, valor)
        if cambia_categoria:
            # La verificación con IA era para la categoría anterior.
            material.verificado_ia = False
        if clasificacion is not None:
            self._vincular_clasificacion(material, clasificacion)

        self.motor.sincronizar_material(material, OrigenCoincidencia.PUBLICACION_MATERIAL)
        self.db.commit()
        self.db.refresh(material)
        return material

    def cambiar_disponibilidad(
        self, empresa: Empresa, material_id: int, disponibilidad: DisponibilidadMaterial
    ) -> MaterialSobrante:
        material = self.obtener_propio(empresa, material_id)
        if material.disponibilidad == DisponibilidadMaterial.RETIRADO:
            raise ReglaNegocioError("El material fue retirado; publícalo de nuevo.")
        material.disponibilidad = disponibilidad
        self.motor.sincronizar_material(material, OrigenCoincidencia.PUBLICACION_MATERIAL)
        self.db.commit()
        return material

    def retirar(self, empresa: Empresa, material_id: int) -> None:
        """Retira la publicación. Se conserva el registro por el historial de solicitudes."""
        material = self.obtener_propio(empresa, material_id)
        material.disponibilidad = DisponibilidadMaterial.RETIRADO
        self.motor.sincronizar_material(material, OrigenCoincidencia.PUBLICACION_MATERIAL)
        self.db.commit()

    # ------------------------------------------------------------------------ apoyo

    @staticmethod
    def _campos(datos: MaterialSobranteRequest) -> dict:
        campos = datos.model_dump(exclude={"dimensiones", "clasificacion_id"})
        dimensiones = datos.dimensiones.model_dump() if datos.dimensiones else {}
        campos["dimensiones"] = Dimensiones(**dimensiones)
        return campos

    def _clasificacion_utilizable(
        self, usuario: Usuario, clasificacion_id: int | None, material_id: int | None = None
    ) -> ClasificacionMaterial | None:
        if clasificacion_id is None:
            return None
        clasificacion = self.clasificaciones.obtener(clasificacion_id)
        if clasificacion is None or clasificacion.usuario_id != usuario.id:
            raise RecursoNoEncontradoError("Reconocimiento con IA no encontrado.")
        if clasificacion.material_id is not None and clasificacion.material_id != material_id:
            raise ReglaNegocioError("Ese reconocimiento ya está asociado a otro material.")
        return clasificacion

    def _vincular_clasificacion(
        self, material: MaterialSobrante, clasificacion: ClasificacionMaterial
    ) -> None:
        """Asocia la foto reconocida al material y marca la verificación.

        Publicar con una categoría equivale a que el usuario confirme (si coincide con
        la que propuso la IA) o corrija (si es distinta) el reconocimiento.
        """
        if clasificacion.estado_verificacion == EstadoVerificacion.PENDIENTE:
            coincide = clasificacion.categoria_predicha_id == material.categoria_id
            clasificacion.estado_verificacion = (
                EstadoVerificacion.CONFIRMADA if coincide else EstadoVerificacion.CORREGIDA
            )
            clasificacion.categoria_confirmada_id = material.categoria_id

        ya_vinculada = clasificacion.material_id == material.id
        clasificacion.material_id = material.id
        material.verificado_ia = (
            clasificacion.estado_verificacion == EstadoVerificacion.CONFIRMADA
            and clasificacion.categoria_confirmada_id == material.categoria_id
        )
        if not ya_vinculada:
            self.fotos.agregar_desde_ruta(
                material,
                clasificacion.ruta_imagen,
                clasificacion.tipo_mime,
                clasificacion.tamano_bytes,
            )
