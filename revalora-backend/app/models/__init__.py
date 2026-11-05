"""Modelos SQLAlchemy de REVALORA.

Todos los modelos se importan aquí para que SQLAlchemy resuelva las relaciones
y para que Alembic los detecte al generar migraciones
(uv run alembic revision --autogenerate).
"""

from app.models.base import Base
from app.models.buscador import BusquedaFabricacion, MaterialRequerido
from app.models.coincidencia import Coincidencia, OrigenCoincidencia
from app.models.empresa import ActividadEconomica, Empresa, TipoEmpresa, Ubicacion
from app.models.ia import ClasificacionMaterial, EstadoVerificacion
from app.models.material import (
    CategoriaMaterial,
    Dimensiones,
    DisponibilidadMaterial,
    EstadoMaterial,
    FotoMaterial,
    MaterialSobrante,
    TipoOferta,
    UnidadMedida,
)
from app.models.necesidad import EstadoNecesidad, NecesidadMaterial
from app.models.oportunidad import MaterialFaltante, OportunidadProductiva, ProductoSugerido
from app.models.transaccion import EstadoSolicitud, HistorialOperacion, Solicitud, TipoSolicitud
from app.models.usuario import Rol, Usuario

__all__ = [
    "ActividadEconomica",
    "Base",
    "BusquedaFabricacion",
    "CategoriaMaterial",
    "ClasificacionMaterial",
    "Coincidencia",
    "Dimensiones",
    "DisponibilidadMaterial",
    "Empresa",
    "EstadoMaterial",
    "EstadoNecesidad",
    "EstadoSolicitud",
    "EstadoVerificacion",
    "FotoMaterial",
    "HistorialOperacion",
    "MaterialFaltante",
    "MaterialRequerido",
    "MaterialSobrante",
    "NecesidadMaterial",
    "OportunidadProductiva",
    "OrigenCoincidencia",
    "ProductoSugerido",
    "Rol",
    "Solicitud",
    "TipoEmpresa",
    "TipoOferta",
    "TipoSolicitud",
    "UnidadMedida",
    "Ubicacion",
    "Usuario",
]
