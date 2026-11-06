"""Cliente HTTP del servicio de IA (revalora-ia-service).

Es el único punto de contacto con el servicio de IA. La URL y el tiempo de
espera se configuran en app.core.config (IA_SERVICE_URL, IA_SERVICE_TIMEOUT).
El formato de las peticiones y respuestas está en docs/contrato-api-ia.md.
"""

import logging
from functools import lru_cache
from typing import Annotated, Any, TypeVar

import httpx
from fastapi import Depends
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.exceptions import IaServiceError
from app.schemas.ia_schema import (
    RespuestaOportunidadesIA,
    RespuestaRecomendacionIA,
    RespuestaReconocimientoIA,
)

logger = logging.getLogger(__name__)

R = TypeVar("R", bound=BaseModel)

PREFIJO_API = "/api/v1"


class IaServiceClient:
    def __init__(
        self, base_url: str, timeout: float, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._http = httpx.Client(
            base_url=base_url.rstrip("/") + PREFIJO_API, timeout=timeout, transport=transport
        )

    def _post(self, ruta: str, modelo: type[R], **kwargs: Any) -> R:
        try:
            respuesta = self._http.post(ruta, **kwargs)
            respuesta.raise_for_status()
            return modelo.model_validate(respuesta.json())
        except httpx.TimeoutException as exc:
            logger.warning("El servicio de IA no respondió a tiempo (%s)", ruta)
            raise IaServiceError("El servicio de IA no respondió a tiempo.") from exc
        except httpx.HTTPStatusError as exc:
            logger.warning("El servicio de IA respondió %s en %s", exc.response.status_code, ruta)
            raise IaServiceError("El servicio de IA devolvió un error.") from exc
        except httpx.HTTPError as exc:
            logger.warning("No se pudo conectar con el servicio de IA: %s", exc)
            raise IaServiceError("No se pudo conectar con el servicio de IA.") from exc
        except (ValidationError, ValueError) as exc:
            logger.warning("Respuesta inesperada del servicio de IA en %s: %s", ruta, exc)
            raise IaServiceError("El servicio de IA devolvió una respuesta inválida.") from exc

    def reconocer_material(
        self, contenido: bytes, nombre_archivo: str, tipo_mime: str
    ) -> RespuestaReconocimientoIA:
        """Clasifica el material de una foto."""
        return self._post(
            "/reconocimiento",
            RespuestaReconocimientoIA,
            files={"imagen": (nombre_archivo, contenido, tipo_mime)},
        )

    def recomendar_materiales(self, descripcion: str) -> RespuestaRecomendacionIA:
        """Deduce los materiales necesarios para fabricar el producto descrito."""
        return self._post(
            "/recomendacion", RespuestaRecomendacionIA, json={"descripcion": descripcion}
        )

    def sugerir_oportunidades(
        self, materiales: list[str], max_productos: int
    ) -> RespuestaOportunidadesIA:
        """Sugiere productos que se pueden fabricar con los materiales indicados."""
        return self._post(
            "/oportunidades",
            RespuestaOportunidadesIA,
            json={"materiales": materiales, "max_productos": max_productos},
        )

    def cerrar(self) -> None:
        self._http.close()


@lru_cache
def obtener_ia_client() -> IaServiceClient:
    """Instancia compartida del cliente (reutiliza las conexiones HTTP)."""
    return IaServiceClient(settings.ia_service_url, settings.ia_service_timeout)


IaClientDep = Annotated[IaServiceClient, Depends(obtener_ia_client)]
