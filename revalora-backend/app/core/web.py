"""Plantillas Jinja2 y archivos estáticos (vistas del MVC)."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings

APP_DIR = Path(__file__).resolve().parents[1]

templates = Jinja2Templates(directory=APP_DIR / "templates")


def montar_archivos(app: FastAPI) -> None:
    """Sirve /static (css, js, img) y /uploads (fotos subidas por los usuarios)."""
    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

    settings.ruta_uploads.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.ruta_uploads), name="uploads")
