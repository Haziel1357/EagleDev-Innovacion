"""Solicitudes de compra o intercambio: creación, aceptación y rechazo.

Ciclo de vida:

    PENDIENTE --aceptar--> ACEPTADA --completar--> COMPLETADA
        |
        +--rechazar--> RECHAZADA
        +--cancelar--> CANCELADA

Al aceptar se descuenta la cantidad del material; si se agota, las demás solicitudes
pendientes de ese material se rechazan automáticamente.
"""

from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.exceptions import AccesoDenegadoError, RecursoNoEncontradoError, ReglaNegocioError
from app.models import (
    DisponibilidadMaterial,
    Empresa,
    EstadoSolicitud,
    MaterialSobrante,
    OrigenCoincidencia,
    Solicitud,
    TipoSolicitud,
    Usuario,
)
from app.repositories.material.material_sobrante_repository import MaterialSobranteRepository
from app.repositories.transaccion.solicitud_repository import SolicitudRepository
from app.schemas.transaccion_schema import SolicitudRequest
from app.services.coincidencia.motor_coincidencia_service import MotorCoincidenciaService
from app.services.transaccion.historial_operacion_service import HistorialOperacionService

MENSAJE_AGOTADO = "Rechazada automáticamente: el material ya no tiene cantidad disponible."


class SolicitudService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.solicitudes = SolicitudRepository(db)
        self.materiales = MaterialSobranteRepository(db)
        self.historial = HistorialOperacionService(db)
        self.motor = MotorCoincidenciaService(db)

    # ---------------------------------------------------------------------- consultas

    def obtener(self, empresa: Empresa, solicitud_id: int) -> Solicitud:
        solicitud = self.solicitudes.obtener(solicitud_id)
        if solicitud is None:
            raise RecursoNoEncontradoError("Solicitud no encontrada.")
        if not solicitud.participa(empresa.id):
            raise AccesoDenegadoError("No participas en esta solicitud.")
        return solicitud

    def enviadas(
        self, empresa: Empresa, estado: EstadoSolicitud | None, offset: int, limite: int
    ) -> tuple[Sequence[Solicitud], int]:
        return self.solicitudes.enviadas(empresa.id, estado, offset, limite)

    def recibidas(
        self, empresa: Empresa, estado: EstadoSolicitud | None, offset: int, limite: int
    ) -> tuple[Sequence[Solicitud], int]:
        return self.solicitudes.recibidas(empresa.id, estado, offset, limite)

    # -------------------------------------------------------------------- operaciones

    def crear(self, usuario: Usuario, empresa: Empresa, datos: SolicitudRequest) -> Solicitud:
        material = self.materiales.obtener(datos.material_id)
        if material is None or material.disponibilidad == DisponibilidadMaterial.RETIRADO:
            raise RecursoNoEncontradoError("Material no encontrado.")
        if material.empresa_id == empresa.id:
            raise ReglaNegocioError("No puedes enviar una solicitud a tu propio material.")
        if not material.esta_disponible:
            raise ReglaNegocioError("El material no está disponible.")
        if datos.tipo.tipo_oferta != material.tipo_oferta:
            raise ReglaNegocioError(
                f"Este material se ofrece para {material.tipo_oferta.value.lower()}; "
                f"no admite solicitudes de {datos.tipo.value.lower()}."
            )
        if datos.cantidad > material.cantidad:
            raise ReglaNegocioError(
                f"La cantidad solicitada supera la disponible ({material.cantidad})."
            )
        if self.solicitudes.existe_pendiente(material.id, empresa.id):
            raise ReglaNegocioError("Ya tienes una solicitud pendiente para este material.")

        material_ofrecido = None
        if datos.tipo == TipoSolicitud.INTERCAMBIO:
            material_ofrecido = self._material_ofrecido(empresa, datos.material_ofrecido_id)

        solicitud = Solicitud(
            material=material,
            empresa_solicitante=empresa,
            tipo=datos.tipo,
            cantidad=datos.cantidad,
            mensaje=datos.mensaje,
            precio_ofrecido=datos.precio_ofrecido if datos.tipo == TipoSolicitud.COMPRA else None,
            material_ofrecido=material_ofrecido,
            estado=EstadoSolicitud.PENDIENTE,
        )
        self.solicitudes.agregar(solicitud)
        self.historial.registrar(solicitud, usuario, None, EstadoSolicitud.PENDIENTE, datos.mensaje)
        self.db.commit()
        return solicitud

    def aceptar(
        self, usuario: Usuario, empresa: Empresa, solicitud_id: int, comentario: str | None
    ) -> Solicitud:
        solicitud = self._como_ofertante(empresa, solicitud_id)
        self._exigir_estado(solicitud, EstadoSolicitud.PENDIENTE)
        material = solicitud.material
        if not material.esta_disponible:
            raise ReglaNegocioError("El material ya no está disponible.")
        if solicitud.cantidad > material.cantidad:
            raise ReglaNegocioError(
                f"La cantidad solicitada supera la disponible ({material.cantidad})."
            )
        if solicitud.material_ofrecido is not None:
            if not solicitud.material_ofrecido.esta_disponible:
                raise ReglaNegocioError("El material ofrecido a cambio ya no está disponible.")
            solicitud.material_ofrecido.disponibilidad = DisponibilidadMaterial.RESERVADO
            self.motor.sincronizar_material(
                solicitud.material_ofrecido, OrigenCoincidencia.PUBLICACION_MATERIAL
            )

        material.cantidad -= solicitud.cantidad
        self._cambiar_estado(solicitud, usuario, EstadoSolicitud.ACEPTADA, comentario)

        if material.cantidad <= 0:
            material.disponibilidad = DisponibilidadMaterial.AGOTADO
            for otra in self.solicitudes.pendientes_de_material(
                material.id, excluir_id=solicitud.id
            ):
                self._cambiar_estado(otra, usuario, EstadoSolicitud.RECHAZADA, MENSAJE_AGOTADO)
        self.motor.sincronizar_material(material, OrigenCoincidencia.PUBLICACION_MATERIAL)
        self.db.commit()
        return solicitud

    def rechazar(
        self, usuario: Usuario, empresa: Empresa, solicitud_id: int, comentario: str | None
    ) -> Solicitud:
        solicitud = self._como_ofertante(empresa, solicitud_id)
        self._exigir_estado(solicitud, EstadoSolicitud.PENDIENTE)
        self._cambiar_estado(solicitud, usuario, EstadoSolicitud.RECHAZADA, comentario)
        self.db.commit()
        return solicitud

    def cancelar(
        self, usuario: Usuario, empresa: Empresa, solicitud_id: int, comentario: str | None
    ) -> Solicitud:
        solicitud = self.obtener(empresa, solicitud_id)
        if solicitud.empresa_solicitante_id != empresa.id:
            raise AccesoDenegadoError("Solo quien envió la solicitud puede cancelarla.")
        self._exigir_estado(solicitud, EstadoSolicitud.PENDIENTE)
        self._cambiar_estado(solicitud, usuario, EstadoSolicitud.CANCELADA, comentario)
        self.db.commit()
        return solicitud

    def completar(
        self, usuario: Usuario, empresa: Empresa, solicitud_id: int, comentario: str | None
    ) -> Solicitud:
        """Cualquiera de las dos empresas marca la entrega como realizada."""
        solicitud = self.obtener(empresa, solicitud_id)
        self._exigir_estado(solicitud, EstadoSolicitud.ACEPTADA)
        if solicitud.material_ofrecido is not None:
            solicitud.material_ofrecido.disponibilidad = DisponibilidadMaterial.AGOTADO
        self._cambiar_estado(solicitud, usuario, EstadoSolicitud.COMPLETADA, comentario)
        self.db.commit()
        return solicitud

    # ------------------------------------------------------------------------ apoyo

    def _como_ofertante(self, empresa: Empresa, solicitud_id: int) -> Solicitud:
        solicitud = self.obtener(empresa, solicitud_id)
        if solicitud.empresa_ofertante_id != empresa.id:
            raise AccesoDenegadoError("Solo la empresa que publicó el material puede responder.")
        return solicitud

    @staticmethod
    def _exigir_estado(solicitud: Solicitud, esperado: EstadoSolicitud) -> None:
        if solicitud.estado != esperado:
            raise ReglaNegocioError(
                f"La solicitud está {solicitud.estado.value.lower()}; "
                f"debe estar {esperado.value.lower()}."
            )

    def _cambiar_estado(
        self, solicitud: Solicitud, usuario: Usuario, nuevo: EstadoSolicitud, comentario: str | None
    ) -> None:
        anterior = solicitud.estado
        solicitud.estado = nuevo
        self.historial.registrar(solicitud, usuario, anterior, nuevo, comentario)

    def _material_ofrecido(self, empresa: Empresa, material_id: int | None) -> MaterialSobrante:
        material = self.materiales.obtener(material_id) if material_id else None
        if material is None or material.empresa_id != empresa.id:
            raise RecursoNoEncontradoError("El material ofrecido no existe en tu empresa.")
        if not material.esta_disponible:
            raise ReglaNegocioError("El material ofrecido a cambio no está disponible.")
        return material
