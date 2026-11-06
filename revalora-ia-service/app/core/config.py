"""Configuración del servicio, leída de variables de entorno o del archivo .env."""

from functools import cached_property
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Carpeta raíz del servicio (revalora-ia-service/).
BASE_DIR = Path(__file__).resolve().parents[2]

# Prefijo de todas las rutas. El backend lo añade en IaServiceClient (PREFIJO_API).
PREFIJO_API = "/api/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    nombre_app: str = "REVALORA IA"
    entorno: Literal["dev", "test", "prod"] = "dev"
    debug: bool = False

    # Reconocimiento de materiales
    #   auto       -> usa CLIP y, si no se puede cargar, el clasificador heurístico.
    #   clip       -> solo CLIP; el servicio no arranca si el modelo no carga.
    #   heuristico -> clasificador por color y textura (rápido, poco preciso).
    modelo_vision: Literal["auto", "clip", "heuristico"] = "auto"
    clip_modelo: str = "openai/clip-vit-base-patch32"
    directorio_modelos: Path = Path("modelos_entrenados")
    # Si es False, el modelo se carga con la primera foto (arranque rápido, primera petición lenta).
    cargar_modelo_al_iniciar: bool = True
    max_predicciones: int = 3

    # Imágenes
    tamano_maximo_imagen_mb: int = 5

    @cached_property
    def ruta_modelos(self) -> Path:
        """Ruta absoluta donde se guardan los modelos descargados."""
        ruta = self.directorio_modelos
        return ruta if ruta.is_absolute() else BASE_DIR / ruta

    @property
    def tamano_maximo_imagen_bytes(self) -> int:
        return self.tamano_maximo_imagen_mb * 1024 * 1024


settings = Settings()
