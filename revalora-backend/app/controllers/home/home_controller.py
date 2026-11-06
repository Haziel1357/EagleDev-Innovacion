"""Controlador: página de inicio y verificación de salud."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.web import renderizar
from app.security.usuario_autenticado import UsuarioPagina

router = APIRouter(tags=["Inicio"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio(request: Request, usuario: UsuarioPagina) -> HTMLResponse:
    return renderizar(request, "home/index.html", usuario)


@router.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
