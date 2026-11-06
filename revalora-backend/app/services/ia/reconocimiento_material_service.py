"""Reconocimiento de materiales: envía la foto a la IA y gestiona la confirmación o corrección del usuario."""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError, ReglaNegocioError
from app.models import ClasificacionMaterial, EstadoVerificacion, Usuario
from app.repositories.ia.clasificacion_material_repository import ClasificacionMaterialRepository
from app.repositories.material.categoria_material_repository import CategoriaMaterialRepository
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.schemas.ia_schema import ConfirmacionClasificacionRequest
from app.services.almacenamiento.almacenamiento_archivo_service import AlmacenamientoArchivoService
from app.services.ia.ia_service_client import IaServiceClient
from app.utils.archivo_util import validar_imagen
from app.utils.constantes import SUBCARPETA_RECONOCIMIENTOS


class ReconocimientoMaterialService:
    def __init__(
        self,
        db: Session,
        ia: IaServiceClient,
        almacenamiento: AlmacenamientoArchivoService | None = None,
    ) -> None:
        self.db = db
        self.ia = ia
        self.almacenamiento = almacenamiento or AlmacenamientoArchivoService()
        self.clasificaciones = ClasificacionMaterialRepository(db)
        self.categorias = CategoriaMaterialRepository(db)
        self.materiales = MaterialSobranteRepository(db)

    def reconocer(
        self,
        usuario: Usuario,
        contenido: bytes,
        tipo_mime: str | None,
        nombre_archivo: str | None,
    ) -> ClasificacionMaterial:
        """Valida la foto, la clasifica con la IA y guarda el resultado como PENDIENTE."""
        extension = validar_imagen(contenido, tipo_mime)
        tipo = (tipo_mime or "").lower()
        # Si la IA falla, no se guarda nada (la excepción se propaga como 502).
        respuesta = self.ia.reconocer_material(
            contenido, nombre_archivo or f"foto{extension}", tipo
        )

        codigos = {respuesta.material, *(p.material for p in respuesta.predicciones)}
        categorias = self.categorias.por_codigos(codigos)
        predicciones = [
            {
                "material": p.material,
                "confianza": p.confianza,
                "categoria_id": c.id if (c := categorias.get(p.material.lower())) else None,
            }
            for p in sorted(respuesta.predicciones, key=lambda p: p.confianza, reverse=True)
        ]

        ruta = self.almacenamiento.guardar(contenido, extension, SUBCARPETA_RECONOCIMIENTOS)
        try:
            clasificacion = self.clasificaciones.agregar(
                ClasificacionMaterial(
                    usuario_id=usuario.id,
                    ruta_imagen=ruta,
                    tipo_mime=tipo,
                    tamano_bytes=len(contenido),
                    material_predicho=respuesta.material.lower(),
                    confianza=respuesta.confianza,
                    predicciones=predicciones,
                    categoria_predicha=categorias.get(respuesta.material.lower()),
                    estado_verificacion=EstadoVerificacion.PENDIENTE,
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.almacenamiento.eliminar(ruta)
            raise
        return clasificacion

    def obtener(self, usuario: Usuario, clasificacion_id: int) -> ClasificacionMaterial:
        clasificacion = self.clasificaciones.obtener(clasificacion_id)
        if clasificacion is None:
            raise RecursoNoEncontradoError("Reconocimiento no encontrado.")
        if clasificacion.usuario_id != usuario.id and not usuario.es_admin:
            raise AccesoDenegadoError("Este reconocimiento no es tuyo.")
        return clasificacion

    def historial(
        self, usuario: Usuario, offset: int, limite: int
    ) -> tuple[Sequence[ClasificacionMaterial], int]:
        return self.clasificaciones.de_usuario(usuario.id, offset, limite)

    def confirmar(
        self, usuario: Usuario, clasificacion_id: int, datos: ConfirmacionClasificacionRequest
    ) -> ClasificacionMaterial:
        """El usuario acepta la categoría propuesta o indica la correcta."""
        clasificacion = self.obtener(usuario, clasificacion_id)

        if datos.categoria_id is None:
            if clasificacion.categoria_predicha_id is None:
                raise ReglaNegocioError(
                    f"La IA propuso '{clasificacion.material_predicho}', que no es una categoría "
                    "de la plataforma. Indica la categoría correcta."
                )
            categoria_id = clasificacion.categoria_predicha_id
        else:
            categoria = self.categorias.obtener(datos.categoria_id)
            if categoria is None or not categoria.activa:
                raise RecursoNoEncontradoError("Categoría de material no encontrada.")
            categoria_id = categoria.id

        clasificacion.categoria_confirmada_id = categoria_id
        clasificacion.estado_verificacion = (
            EstadoVerificacion.CONFIRMADA
            if categoria_id == clasificacion.categoria_predicha_id
            else EstadoVerificacion.CORREGIDA
        )

        material_id = datos.material_id or clasificacion.material_id
        if material_id is not None:
            material = self.materiales.obtener(material_id)
            if material is None or material.empresa_id != usuario.empresa_id:
                raise RecursoNoEncontradoError("Material no encontrado en tu empresa.")
            clasificacion.material_id = material.id
            material.verificado_ia = (
                clasificacion.estado_verificacion == EstadoVerificacion.CONFIRMADA
                and material.categoria_id == categoria_id
            )

        self.db.commit()
        self.db.refresh(clasificacion)
        return clasificacion
