"""Controlador: publicación, listado y detalle de materiales sobrantes."""

from typing import Annotated

from fastapi import APIRouter, File, Query, UploadFile, status

from app.core.database import DbSession
from app.schemas.comun_schema import PaginaResponse
from app.schemas.material_schema import (
    DisponibilidadRequest,
    FiltroMaterialRequest,
    FotoMaterialResponse,
    MaterialSobranteRequest,
    MaterialSobranteResponse,
)
from app.security.usuario_autenticado import EmpresaActual, UsuarioActual, UsuarioOpcional
from app.services.material.foto_material_service import ArchivoSubido, FotoMaterialService
from app.services.material.material_sobrante_service import MaterialSobranteService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/materiales", tags=["Materiales"])


def _respuesta(material) -> MaterialSobranteResponse:
    return MaterialSobranteResponse.model_validate(material)


@router.get("", response_model=PaginaResponse[MaterialSobranteResponse])
def listar_materiales(
    filtro: Annotated[FiltroMaterialRequest, Query()],
    db: DbSession,
    paginacion: PaginacionDep,
) -> PaginaResponse:
    """Materiales disponibles, del más reciente al más antiguo."""
    materiales, total = MaterialSobranteService(db).buscar(
        filtro, offset=paginacion.offset, limite=paginacion.tamano
    )
    return construir_pagina([_respuesta(m) for m in materiales], total, paginacion)


@router.get("/mios", response_model=PaginaResponse[MaterialSobranteResponse])
def mis_materiales(
    empresa: EmpresaActual, db: DbSession, paginacion: PaginacionDep
) -> PaginaResponse:
    """Todos los materiales de mi empresa, en cualquier estado de disponibilidad."""
    materiales, total = MaterialSobranteService(db).de_empresa(
        empresa, paginacion.offset, paginacion.tamano
    )
    return construir_pagina([_respuesta(m) for m in materiales], total, paginacion)


@router.post("", response_model=MaterialSobranteResponse, status_code=status.HTTP_201_CREATED)
def publicar_material(
    datos: MaterialSobranteRequest, usuario: UsuarioActual, empresa: EmpresaActual, db: DbSession
) -> MaterialSobranteResponse:
    """Publica un material sobrante.

    Flujo con foto: sube la foto a `POST /ia/reconocimiento`, revisa la categoría
    sugerida y envía aquí el `clasificacion_id` junto con los datos del material.
    """
    return _respuesta(MaterialSobranteService(db).publicar(usuario, empresa, datos))


@router.get("/{material_id}", response_model=MaterialSobranteResponse)
def obtener_material(
    material_id: int, usuario: UsuarioOpcional, db: DbSession
) -> MaterialSobranteResponse:
    return _respuesta(MaterialSobranteService(db).obtener(material_id, usuario))


@router.put("/{material_id}", response_model=MaterialSobranteResponse)
def actualizar_material(
    material_id: int,
    datos: MaterialSobranteRequest,
    usuario: UsuarioActual,
    empresa: EmpresaActual,
    db: DbSession,
) -> MaterialSobranteResponse:
    return _respuesta(MaterialSobranteService(db).actualizar(usuario, empresa, material_id, datos))


@router.patch("/{material_id}/disponibilidad", response_model=MaterialSobranteResponse)
def cambiar_disponibilidad(
    material_id: int, datos: DisponibilidadRequest, empresa: EmpresaActual, db: DbSession
) -> MaterialSobranteResponse:
    return _respuesta(
        MaterialSobranteService(db).cambiar_disponibilidad(
            empresa, material_id, datos.disponibilidad
        )
    )


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def retirar_material(material_id: int, empresa: EmpresaActual, db: DbSession) -> None:
    """Retira la publicación (deja de mostrarse, pero se conserva su historial)."""
    MaterialSobranteService(db).retirar(empresa, material_id)


# ------------------------------------------------------------------------------ fotos


@router.post(
    "/{material_id}/fotos",
    response_model=list[FotoMaterialResponse],
    status_code=status.HTTP_201_CREATED,
)
async def subir_fotos(
    material_id: int,
    fotos: Annotated[list[UploadFile], File(description="JPG, PNG o WEBP.")],
    empresa: EmpresaActual,
    db: DbSession,
) -> list[FotoMaterialResponse]:
    material = MaterialSobranteService(db).obtener_propio(empresa, material_id)
    archivos = [ArchivoSubido(await f.read(), f.content_type, f.filename) for f in fotos]
    nuevas = FotoMaterialService(db).agregar(material, archivos)
    return [FotoMaterialResponse.model_validate(f) for f in nuevas]


@router.patch("/{material_id}/fotos/{foto_id}/principal", response_model=FotoMaterialResponse)
def marcar_foto_principal(
    material_id: int, foto_id: int, empresa: EmpresaActual, db: DbSession
) -> FotoMaterialResponse:
    material = MaterialSobranteService(db).obtener_propio(empresa, material_id)
    return FotoMaterialResponse.model_validate(
        FotoMaterialService(db).marcar_principal(material, foto_id)
    )


@router.delete("/{material_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_foto(material_id: int, foto_id: int, empresa: EmpresaActual, db: DbSession) -> None:
    material = MaterialSobranteService(db).obtener_propio(empresa, material_id)
    FotoMaterialService(db).eliminar(material, foto_id)
