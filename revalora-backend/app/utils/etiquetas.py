"""Textos legibles de las enumeraciones, para las vistas HTML.

Es la única fuente de estas etiquetas: las plantillas las reciben como variable
global (``etiquetas``) y el JavaScript las lee de ``window.REVALORA.etiquetas``.
"""

from app.models import (
    DisponibilidadMaterial,
    EstadoMaterial,
    EstadoNecesidad,
    EstadoSolicitud,
    EstadoVerificacion,
    TipoEmpresa,
    TipoOferta,
    TipoSolicitud,
    UnidadMedida,
)

ETIQUETAS: dict[str, dict[str, str]] = {
    "tipo_empresa": {
        TipoEmpresa.MICROEMPRESA: "Microempresa",
        TipoEmpresa.PEQUENA_EMPRESA: "Pequeña empresa",
        TipoEmpresa.EMPRENDIMIENTO: "Emprendimiento",
    },
    "estado_material": {
        EstadoMaterial.NUEVO: "Nuevo",
        EstadoMaterial.BUENO: "Bueno",
        EstadoMaterial.REGULAR: "Regular",
        EstadoMaterial.DETERIORADO: "Deteriorado",
    },
    "disponibilidad": {
        DisponibilidadMaterial.DISPONIBLE: "Disponible",
        DisponibilidadMaterial.RESERVADO: "Reservado",
        DisponibilidadMaterial.AGOTADO: "Agotado",
        DisponibilidadMaterial.RETIRADO: "Retirado",
    },
    "tipo_oferta": {
        TipoOferta.VENTA: "Venta",
        TipoOferta.INTERCAMBIO: "Intercambio",
        TipoOferta.APROVECHAMIENTO: "Aprovechamiento",
    },
    "unidad_medida": {
        UnidadMedida.UNIDAD: "Unidades",
        UnidadMedida.KILOGRAMO: "Kilogramos",
        UnidadMedida.METRO: "Metros",
        UnidadMedida.METRO_CUADRADO: "Metros cuadrados",
        UnidadMedida.METRO_CUBICO: "Metros cúbicos",
        UnidadMedida.LITRO: "Litros",
    },
    "unidad_corta": {
        UnidadMedida.UNIDAD: "und.",
        UnidadMedida.KILOGRAMO: "kg",
        UnidadMedida.METRO: "m",
        UnidadMedida.METRO_CUADRADO: "m²",
        UnidadMedida.METRO_CUBICO: "m³",
        UnidadMedida.LITRO: "L",
    },
    "estado_necesidad": {
        EstadoNecesidad.ABIERTA: "Abierta",
        EstadoNecesidad.ATENDIDA: "Atendida",
        EstadoNecesidad.CERRADA: "Cerrada",
    },
    "tipo_solicitud": {
        TipoSolicitud.COMPRA: "Compra",
        TipoSolicitud.INTERCAMBIO: "Intercambio",
        TipoSolicitud.APROVECHAMIENTO: "Aprovechamiento",
    },
    "estado_solicitud": {
        EstadoSolicitud.PENDIENTE: "Pendiente",
        EstadoSolicitud.ACEPTADA: "Aceptada",
        EstadoSolicitud.RECHAZADA: "Rechazada",
        EstadoSolicitud.CANCELADA: "Cancelada",
        EstadoSolicitud.COMPLETADA: "Completada",
    },
    "estado_verificacion": {
        EstadoVerificacion.PENDIENTE: "Pendiente",
        EstadoVerificacion.CONFIRMADA: "Confirmada",
        EstadoVerificacion.CORREGIDA: "Corregida",
    },
}

# Tipo de solicitud que corresponde a cada tipo de oferta de un material.
SOLICITUD_POR_OFERTA: dict[str, str] = {s.tipo_oferta.value: s.value for s in TipoSolicitud}


def etiquetas_json() -> dict[str, dict[str, str]]:
    """Etiquetas con claves de texto plano, listas para serializar a JSON."""
    return {grupo: {str(k): v for k, v in valores.items()} for grupo, valores in ETIQUETAS.items()}
