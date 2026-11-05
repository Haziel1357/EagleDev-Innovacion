"""Lógica de negocio de las fotos de materiales."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.exceptions import RecursoNoEncontradoError, ReglaNegocioError
from app.models import FotoMaterial, MaterialSobrante
from app.repositories.material.foto_material_repository import FotoMaterialRepository
from app.services.almacenamiento.almacenamiento_archivo_service import AlmacenamientoArchivoService
from app.utils.archivo_util import validar_imagen
from app.utils.constantes import MAX_FOTOS_POR_MATERIAL, SUBCARPETA_MATERIALES


@dataclass
class ArchivoSubido:
    contenido: bytes
    tipo_mime: str | None
    nombre: str | None


class FotoMaterialService:
    def __init__(
        self, db: Session, almacenamiento: AlmacenamientoArchivoService | None = None
    ) -> None:
        self.db = db
        self.fotos = FotoMaterialRepository(db)
        self.almacenamiento = almacenamiento or AlmacenamientoArchivoService()

    def agregar(
        self, material: MaterialSobrante, archivos: list[ArchivoSubido]
    ) -> list[FotoMaterial]:
        """Valida y guarda las fotos. La primera foto de un material queda como principal."""
        if not archivos:
            raise ReglaNegocioError("Adjunta al menos una foto.")
        actuales = self.fotos.contar_de_material(material.id)
        if actuales + len(archivos) > MAX_FOTOS_POR_MATERIAL:
            raise ReglaNegocioError(
                f"Un material admite como máximo {MAX_FOTOS_POR_MATERIAL} fotos "
                f"(ya tiene {actuales})."
            )

        extensiones = [validar_imagen(a.contenido, a.tipo_mime) for a in archivos]
        nuevas: list[FotoMaterial] = []
        guardadas: list[str] = []
        try:
            for indice, (archivo, extension) in enumerate(zip(archivos, extensiones, strict=True)):
                ruta = self.almacenamiento.guardar(
                    archivo.contenido, extension, SUBCARPETA_MATERIALES
                )
                guardadas.append(ruta)
                nuevas.append(
                    FotoMaterial(
                        material=material,
                        ruta=ruta,
                        nombre_original=archivo.nombre,
                        tipo_mime=(archivo.tipo_mime or "").lower(),
                        tamano_bytes=len(archivo.contenido),
                        es_principal=actuales == 0 and indice == 0,
                    )
                )
            self.db.add_all(nuevas)
            self.db.commit()
        except Exception:
            self.db.rollback()
            for ruta in guardadas:
                self.almacenamiento.eliminar(ruta)
            raise
        self.db.refresh(material)
        return nuevas

    def agregar_desde_ruta(
        self, material: MaterialSobrante, ruta_origen: str, tipo_mime: str, tamano: int
    ) -> FotoMaterial:
        """Copia una imagen ya guardada (p. ej. la del reconocimiento con IA) como foto principal.

        No confirma la transacción: la usa el servicio de materiales dentro de su operación.
        """
        for foto in material.fotos:
            foto.es_principal = False
        ruta = self.almacenamiento.copiar(ruta_origen, SUBCARPETA_MATERIALES)
        foto = FotoMaterial(
            material=material,
            ruta=ruta,
            nombre_original=None,
            tipo_mime=tipo_mime,
            tamano_bytes=tamano,
            es_principal=True,
        )
        self.db.add(foto)
        return foto

    def marcar_principal(self, material: MaterialSobrante, foto_id: int) -> FotoMaterial:
        foto = self._de_material(material, foto_id)
        for otra in material.fotos:
            otra.es_principal = otra.id == foto.id
        self.db.commit()
        return foto

    def eliminar(self, material: MaterialSobrante, foto_id: int) -> None:
        foto = self._de_material(material, foto_id)
        era_principal = foto.es_principal
        ruta = foto.ruta
        material.fotos.remove(foto)
        if era_principal and material.fotos:
            material.fotos[0].es_principal = True
        self.db.commit()
        self.almacenamiento.eliminar(ruta)

    def _de_material(self, material: MaterialSobrante, foto_id: int) -> FotoMaterial:
        foto = self.fotos.de_material(material.id, foto_id)
        if foto is None:
            raise RecursoNoEncontradoError("Foto no encontrada.")
        return foto
