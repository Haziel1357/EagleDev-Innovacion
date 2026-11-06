"""Controlador web: página de inicio."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.web import templates

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def inicio(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "home/index.html")
