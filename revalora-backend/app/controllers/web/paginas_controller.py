"""Controlador web: páginas HTML de la aplicación (vistas Jinja2).

Las páginas van sin prefijo (``/materiales``) y la API JSON bajo ``/api/v1``
(``/api/v1/materiales``). Cada página entrega el esqueleto HTML y el JavaScript
de su módulo (``static/js/modulos``) carga los datos desde la API usando la
cookie de sesión.
"""

from urllib.parse import quote

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.core.web import renderizar
from app.models import Usuario
from app.security.usuario_autenticado import UsuarioPagina

router = APIRouter(include_in_schema=False)

RUTA_INGRESAR = "/ingresar"
RUTA_EMPRESA = "/empresa"
RUTA_CATALOGO = "/materiales"


def _redirigir(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=status.HTTP_303_SEE_OTHER)


def _exigir_sesion(request: Request, usuario: Usuario | None) -> Response | None:
    if usuario is None:
        return _redirigir(f"{RUTA_INGRESAR}?siguiente={quote(request.url.path)}")
    return None


def _exigir_empresa(request: Request, usuario: Usuario | None) -> Response | None:
    if (respuesta := _exigir_sesion(request, usuario)) is not None:
        return respuesta
    if usuario.empresa is None:
        return _redirigir(f"{RUTA_EMPRESA}?siguiente={quote(request.url.path)}")
    return None


# ------------------------------------------------------------------------ usuario


@router.get("/ingresar", response_class=HTMLResponse)
def pagina_ingresar(request: Request, usuario: UsuarioPagina) -> Response:
    if usuario is not None:
        return _redirigir(RUTA_CATALOGO)
    return renderizar(request, "usuario/login.html", usuario)


@router.get("/registro", response_class=HTMLResponse)
def pagina_registro(request: Request, usuario: UsuarioPagina) -> Response:
    if usuario is not None:
        return _redirigir(RUTA_CATALOGO)
    return renderizar(request, "usuario/registro.html", usuario)


@router.get("/perfil", response_class=HTMLResponse)
def pagina_perfil(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_sesion(request, usuario) or renderizar(request, "usuario/perfil.html", usuario)


# ------------------------------------------------------------------------ empresa


@router.get("/empresa", response_class=HTMLResponse)
def pagina_mi_empresa(request: Request, usuario: UsuarioPagina) -> Response:
    """Registro (o edición) de la empresa del usuario."""
    return _exigir_sesion(request, usuario) or renderizar(
        request, "empresa/formulario.html", usuario
    )


@router.get("/empresas/{empresa_id}", response_class=HTMLResponse)
def pagina_empresa(request: Request, empresa_id: int, usuario: UsuarioPagina) -> Response:
    return renderizar(request, "empresa/detalle.html", usuario, empresa_id=empresa_id)


# ---------------------------------------------------------------------- materiales


@router.get("/materiales", response_class=HTMLResponse)
def pagina_materiales(request: Request, usuario: UsuarioPagina) -> Response:
    """Catálogo de materiales disponibles (búsqueda tradicional con filtros)."""
    return renderizar(request, "material/lista.html", usuario)


@router.get("/materiales/publicar", response_class=HTMLResponse)
def pagina_publicar_material(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "material/formulario.html", usuario, material_id=None
    )


@router.get("/materiales/{material_id}", response_class=HTMLResponse)
def pagina_material(request: Request, material_id: int, usuario: UsuarioPagina) -> Response:
    return renderizar(request, "material/detalle.html", usuario, material_id=material_id)


@router.get("/materiales/{material_id}/editar", response_class=HTMLResponse)
def pagina_editar_material(request: Request, material_id: int, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "material/formulario.html", usuario, material_id=material_id
    )


@router.get("/mis-materiales", response_class=HTMLResponse)
def pagina_mis_materiales(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "material/mis-materiales.html", usuario
    )


# --------------------------------------------------------------------- necesidades


@router.get("/necesidades", response_class=HTMLResponse)
def pagina_necesidades(request: Request, usuario: UsuarioPagina) -> Response:
    """Necesidades abiertas que publican las empresas."""
    return renderizar(request, "necesidad/lista.html", usuario)


@router.get("/necesidades/publicar", response_class=HTMLResponse)
def pagina_publicar_necesidad(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "necesidad/formulario.html", usuario, necesidad_id=None
    )


@router.get("/necesidades/{necesidad_id}", response_class=HTMLResponse)
def pagina_necesidad(request: Request, necesidad_id: int, usuario: UsuarioPagina) -> Response:
    return renderizar(request, "necesidad/detalle.html", usuario, necesidad_id=necesidad_id)


@router.get("/necesidades/{necesidad_id}/editar", response_class=HTMLResponse)
def pagina_editar_necesidad(
    request: Request, necesidad_id: int, usuario: UsuarioPagina
) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "necesidad/formulario.html", usuario, necesidad_id=necesidad_id
    )


@router.get("/mis-necesidades", response_class=HTMLResponse)
def pagina_mis_necesidades(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "necesidad/mis-necesidades.html", usuario
    )


# -------------------------------------------------------------------- transacciones


@router.get("/solicitudes", response_class=HTMLResponse)
def pagina_solicitudes(request: Request, usuario: UsuarioPagina) -> Response:
    """Solicitudes recibidas y enviadas por la empresa del usuario."""
    return _exigir_empresa(request, usuario) or renderizar(
        request, "transaccion/solicitudes.html", usuario
    )


@router.get("/solicitudes/{solicitud_id}", response_class=HTMLResponse)
def pagina_solicitud(request: Request, solicitud_id: int, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "transaccion/detalle-solicitud.html", usuario, solicitud_id=solicitud_id
    )


@router.get("/historial", response_class=HTMLResponse)
def pagina_historial(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "transaccion/historial.html", usuario
    )


# ---------------------------------------------------------- buscador y coincidencias


@router.get("/buscador", response_class=HTMLResponse)
def pagina_buscador(request: Request, usuario: UsuarioPagina) -> Response:
    """Buscador inteligente: describe lo que quieres fabricar."""
    return _exigir_sesion(request, usuario) or renderizar(
        request, "buscador/buscador-inteligente.html", usuario
    )


@router.get("/coincidencias", response_class=HTMLResponse)
def pagina_coincidencias(request: Request, usuario: UsuarioPagina) -> Response:
    """Todas las coincidencias de mis materiales y mis necesidades."""
    return _exigir_empresa(request, usuario) or renderizar(
        request, "coincidencia/lista.html", usuario
    )


# -------------------------------------------------------------------- oportunidades


@router.get("/oportunidades", response_class=HTMLResponse)
def pagina_oportunidades(request: Request, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "oportunidad/lista.html", usuario
    )


@router.get("/oportunidades/{oportunidad_id}", response_class=HTMLResponse)
def pagina_oportunidad(request: Request, oportunidad_id: int, usuario: UsuarioPagina) -> Response:
    return _exigir_empresa(request, usuario) or renderizar(
        request, "oportunidad/detalle.html", usuario, oportunidad_id=oportunidad_id
    )
