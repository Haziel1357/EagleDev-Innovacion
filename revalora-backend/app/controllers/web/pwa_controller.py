"""Controlador web: aplicación web progresiva (PWA).

- ``/manifest.webmanifest``: nombre, íconos y colores con los que se instala la app.
- ``/sw.js``: service worker. Va en la raíz (y no en ``/static``) porque solo controla
  las páginas que quedan por debajo de su ruta.
- ``/sin-conexion``: página que el service worker muestra al navegar sin red.
"""

import hashlib
from functools import cache

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.core.config import settings
from app.core.web import APP_DIR, COLOR_TEMA, renderizar, templates

router = APIRouter(include_in_schema=False)

# Fondo de la pantalla de bienvenida de la app instalada: --fondo de main.css.
COLOR_FONDO = "#faf8f3"

DESCRIPCION = (
    "Conecta a las empresas que generan materiales sobrantes con quienes los necesitan "
    "como materia prima."
)

# Lo que necesita la página sin conexión. El resto de /static se guarda a medida que se usa.
_PRECACHE_ESTATICOS = ("css/main.css", "css/componentes.css", "img/logos/favicon.svg")

# Atajos del ícono de la app instalada (clic derecho o pulsación larga).
_ATAJOS = (
    ("Explorar materiales", "pagina_materiales"),
    ("Publicar un sobrante", "pagina_publicar_material"),
    ("Necesidades", "pagina_necesidades"),
    ("Buscador IA", "pagina_buscador"),
)


def _ruta(request: Request, nombre: str, **parametros: str) -> str:
    """Ruta relativa (sin dominio) de una página o archivo estático."""
    return request.url_for(nombre, **parametros).path


@cache
def _version() -> str:
    """Huella de /static y de las plantillas de la PWA. Si algo cambia, cambia el service
    worker: el navegador lo reinstala y descarta lo que tenía guardado."""
    huella = hashlib.sha256()
    for carpeta in (APP_DIR / "static", APP_DIR / "templates" / "pwa"):
        for archivo in sorted(p for p in carpeta.rglob("*") if p.is_file()):
            huella.update(archivo.relative_to(APP_DIR).as_posix().encode())
            huella.update(archivo.read_bytes())
    return huella.hexdigest()[:12]


@router.get("/manifest.webmanifest")
def manifest(request: Request) -> JSONResponse:
    def icono(archivo: str, lado: int, proposito: str = "any") -> dict[str, str]:
        return {
            "src": _ruta(request, "static", path=f"img/logos/{archivo}"),
            "sizes": f"{lado}x{lado}",
            "type": "image/png",
            "purpose": proposito,
        }

    inicio = _ruta(request, "inicio")
    return JSONResponse(
        {
            "id": inicio,
            "name": f"{settings.nombre_app} · Materiales sobrantes con nueva vida",
            "short_name": settings.nombre_app,
            "description": DESCRIPCION,
            "lang": "es",
            "dir": "ltr",
            "start_url": inicio,
            "scope": inicio,
            "display": "standalone",
            "background_color": COLOR_FONDO,
            "theme_color": COLOR_TEMA,
            "categories": ["business", "productivity"],
            "icons": [
                icono("icono-192.png", 192),
                icono("icono-512.png", 512),
                icono("icono-maskable-512.png", 512, "maskable"),
            ],
            "shortcuts": [
                {
                    "name": nombre,
                    "url": _ruta(request, pagina),
                    "icons": [icono("icono-192.png", 192)],
                }
                for nombre, pagina in _ATAJOS
            ],
        },
        media_type="application/manifest+json",
    )


@router.get("/sw.js")
def service_worker(request: Request) -> Response:
    url_sin_conexion = _ruta(request, "pagina_sin_conexion")
    return templates.TemplateResponse(
        request,
        "pwa/sw.js",
        {
            "version": _version(),
            "url_sin_conexion": url_sin_conexion,
            "prefijo_estaticos": _ruta(request, "static", path=""),
            "precache": [
                url_sin_conexion,
                *(_ruta(request, "static", path=archivo) for archivo in _PRECACHE_ESTATICOS),
            ],
        },
        media_type="text/javascript",
        # Que el navegador compruebe siempre si hay una versión nueva.
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/sin-conexion", response_class=HTMLResponse)
def pagina_sin_conexion(request: Request) -> HTMLResponse:
    return renderizar(request, "pwa/sin-conexion.html")
