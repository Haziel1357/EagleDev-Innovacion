"""Controlador: página de inicio y verificación de salud."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.web import templates

router = APIRouter(tags=["Inicio"])


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def inicio(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home/index.html")


@router.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}
