"""Reúne los routers de todos los controladores.

- ``api_router``: API REST en JSON, bajo ``/api/v1`` (controllers/api/).
- ``web_router``: vistas HTML con Jinja2, sin prefijo (controllers/web/).

Separarlos evita que una página y un endpoint compartan ruta
(por ejemplo, la página ``/materiales`` y el JSON ``/api/v1/materiales``).
"""

from fastapi import APIRouter

from app.controllers.api import salud_controller
from app.controllers.api.buscador import (
    buscador_inteligente_controller,
    busqueda_tradicional_controller,
)
from app.controllers.api.coincidencia import coincidencia_controller
from app.controllers.api.empresa import empresa_controller
from app.controllers.api.ia import reconocimiento_material_controller
from app.controllers.api.material import (
    categoria_material_controller,
    material_sobrante_controller,
)
from app.controllers.api.necesidad import necesidad_material_controller
from app.controllers.api.oportunidad import oportunidad_productiva_controller
from app.controllers.api.transaccion import historial_operacion_controller, solicitud_controller
from app.controllers.api.usuario import auth_controller, usuario_controller
from app.controllers.web import paginas_controller
from app.controllers.web.home import home_controller
from app.core.config import PREFIJO_API

_CONTROLADORES_API = (
    salud_controller,
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

_CONTROLADORES_WEB = (home_controller, paginas_controller)

api_router = APIRouter(prefix=PREFIJO_API)
for controlador in _CONTROLADORES_API:
    api_router.include_router(controlador.router)

web_router = APIRouter()
for controlador in _CONTROLADORES_WEB:
    web_router.include_router(controlador.router)
