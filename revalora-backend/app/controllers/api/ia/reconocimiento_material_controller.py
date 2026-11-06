"""Controlador: reconocimiento del material de una foto y confirmación de la clasificación."""

from typing import Annotated

from fastapi import APIRouter, File, UploadFile, status

from app.core.database import DbSession
from app.schemas.comun_schema import PaginaResponse
from app.schemas.ia_schema import ConfirmacionClasificacionRequest, ReconocimientoResponse
from app.security.usuario_autenticado import UsuarioActual
from app.services.ia.ia_service_client import IaClientDep
from app.services.ia.reconocimiento_material_service import ReconocimientoMaterialService
from app.utils.paginacion import PaginacionDep, construir_pagina

router = APIRouter(prefix="/ia", tags=["Reconocimiento con IA"])


@router.post(
    "/reconocimiento", response_model=ReconocimientoResponse, status_code=status.HTTP_201_CREATED
)
async def reconocer_material(
    imagen: Annotated[UploadFile, File(description="Foto del material (JPG, PNG o WEBP).")],
    usuario: UsuarioActual,
    db: DbSession,
    ia: IaClientDep,
) -> ReconocimientoResponse:
    """Clasifica el material de la foto (madera, cartón, plástico, tela, metal…).

    Devuelve la categoría sugerida y la confianza. El usuario la confirma o corrige con
    `POST /ia/clasificaciones/{id}/confirmar`, o directamente al publicar el material
    enviando el `clasificacion_id`.
    """
    contenido = await imagen.read()
    clasificacion = ReconocimientoMaterialService(db, ia).reconocer(
        usuario, contenido, imagen.content_type, imagen.filename
    )
    return ReconocimientoResponse.model_validate(clasificacion)


@router.get("/clasificaciones", response_model=PaginaResponse[ReconocimientoResponse])
def mis_clasificaciones(
    usuario: UsuarioActual, db: DbSession, ia: IaClientDep, paginacion: PaginacionDep
) -> PaginaResponse:
    clasificaciones, total = ReconocimientoMaterialService(db, ia).historial(
        usuario, paginacion.offset, paginacion.tamano
    )
    return construir_pagina(
        [ReconocimientoResponse.model_validate(c) for c in clasificaciones], total, paginacion
    )


@router.get("/clasificaciones/{clasificacion_id}", response_model=ReconocimientoResponse)
def obtener_clasificacion(
    clasificacion_id: int, usuario: UsuarioActual, db: DbSession, ia: IaClientDep
) -> ReconocimientoResponse:
    return ReconocimientoResponse.model_validate(
        ReconocimientoMaterialService(db, ia).obtener(usuario, clasificacion_id)
    )


@router.post("/clasificaciones/{clasificacion_id}/confirmar", response_model=ReconocimientoResponse)
def confirmar_clasificacion(
    clasificacion_id: int,
    datos: ConfirmacionClasificacionRequest,
    usuario: UsuarioActual,
    db: DbSession,
    ia: IaClientDep,
) -> ReconocimientoResponse:
    """Acepta la categoría propuesta por la IA (sin `categoria_id`) o la corrige."""
    return ReconocimientoResponse.model_validate(
        ReconocimientoMaterialService(db, ia).confirmar(usuario, clasificacion_id, datos)
    )
