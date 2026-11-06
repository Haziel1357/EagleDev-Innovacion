"""Plantillas Jinja2 y archivos estáticos (vistas del MVC)."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import PREFIJO_API, settings
from app.utils.etiquetas import ETIQUETAS, SOLICITUD_POR_OFERTA, etiquetas_json

if TYPE_CHECKING:
    from app.models import Usuario

APP_DIR = Path(__file__).resolve().parents[1]

templates = Jinja2Templates(directory=APP_DIR / "templates")
templates.env.globals.update(
    nombre_app=settings.nombre_app,
    prefijo_api=PREFIJO_API,
    etiquetas=ETIQUETAS,
    etiquetas_json=etiquetas_json(),
    solicitud_por_oferta=SOLICITUD_POR_OFERTA,
    tamano_maximo_archivo_mb=settings.tamano_maximo_archivo_mb,
)


def datos_sesion(usuario: "Usuario | None") -> dict[str, Any] | None:
    """Datos mínimos del usuario que necesitan las vistas (navbar y JavaScript)."""
    if usuario is None:
        return None
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol_nombre,
        "empresa_id": usuario.empresa_id,
        "empresa_nombre": usuario.empresa.nombre if usuario.empresa else None,
    }


def renderizar(
    request: Request, plantilla: str, usuario: "Usuario | None" = None, **contexto: Any
) -> HTMLResponse:
    """Renderiza una vista con la sesión del usuario disponible en la plantilla."""
    return templates.TemplateResponse(
        request, plantilla, {"usuario": usuario, "sesion": datos_sesion(usuario), **contexto}
    )


def montar_archivos(app: FastAPI) -> None:
    """Sirve /static (css, js, img) y /uploads (fotos subidas por los usuarios)."""
    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

    settings.ruta_uploads.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.ruta_uploads), name="uploads")
