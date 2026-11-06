"""Configuración de la aplicación, leída de variables de entorno o del archivo .env."""

from functools import cached_property
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Carpeta raíz del backend (revalora-backend/).
BASE_DIR = Path(__file__).resolve().parents[2]

_SECRET_KEY_DESARROLLO = "solo-para-desarrollo-cambiar-en-produccion"

# Prefijo de todas las rutas de la API REST (JSON). Las vistas HTML van sin prefijo.
PREFIJO_API = "/api/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nombre_app: str = "REVALORA"
    entorno: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False

    # Base de datos
    database_url: str = "postgresql+psycopg://revalora:revalora@localhost:5432/revalora"
    database_echo: bool = False

    # Seguridad
    secret_key: str = _SECRET_KEY_DESARROLLO
    access_token_expire_minutes: int = 60

    # Servicio de IA
    ia_service_url: str = "http://localhost:8000"
    ia_service_timeout: float = 10.0

    # Archivos subidos
    directorio_uploads: Path = Path("uploads")
    tamano_maximo_archivo_mb: int = 5

    @model_validator(mode="after")
    def _validar_produccion(self) -> "Settings":
        if self.entorno == "prod" and self.secret_key == _SECRET_KEY_DESARROLLO:
            raise ValueError("SECRET_KEY debe definirse en producción.")
        if len(self.secret_key.encode()) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres.")
        return self

    @cached_property
    def ruta_uploads(self) -> Path:
        """Ruta absoluta de la carpeta de archivos subidos."""
        ruta = self.directorio_uploads
        return ruta if ruta.is_absolute() else BASE_DIR / ruta


settings = Settings()
