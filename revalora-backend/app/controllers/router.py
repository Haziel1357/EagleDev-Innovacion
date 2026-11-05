"""Reúne los routers de todos los controladores."""

from fastapi import APIRouter

from app.controllers.buscador import buscador_inteligente_controller, busqueda_tradicional_controller
from app.controllers.coincidencia import coincidencia_controller
from app.controllers.empresa import empresa_controller
from app.controllers.home import home_controller
from app.controllers.ia import reconocimiento_material_controller
from app.controllers.material import categoria_material_controller, material_sobrante_controller
from app.controllers.necesidad import necesidad_material_controller
from app.controllers.oportunidad import oportunidad_productiva_controller
from app.controllers.transaccion import historial_operacion_controller, solicitud_controller
from app.controllers.usuario import auth_controller, usuario_controller

_CONTROLADORES = (
    home_controller,
    auth_controller,
    usuario_controller,
    empresa_controller,
    categoria_material_controller,
    material_sobrante_controller,
    necesidad_material_controller,
    reconocimiento_material_controller,
    buscador_inteligente_controller,
    busqueda_tradicional_controller,
    coincidencia_controller,
    solicitud_controller,
    historial_operacion_controller,
    oportunidad_productiva_controller,
)

router = APIRouter()
for controlador in _CONTROLADORES:
    router.include_router(controlador.router)
