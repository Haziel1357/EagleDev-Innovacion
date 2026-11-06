"""Controlador web: página de inicio."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.web import renderizar
from app.security.usuario_autenticado import UsuarioPagina

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def inicio(request: Request, usuario: UsuarioPagina) -> HTMLResponse:
    return renderizar(request, "home/index.html", usuario)
