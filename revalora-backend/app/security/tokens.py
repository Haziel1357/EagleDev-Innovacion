"""Emisión y validación de los tokens de sesión (JWT firmados con HS256)."""

from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.exceptions import NoAutenticadoError

ALGORITMO = "HS256"


def crear_token_acceso(usuario_id: int) -> str:
    ahora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.access_token_expire_minutes),
        "tipo": "acceso",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITMO)


def leer_usuario_id(token: str) -> int:
    """Devuelve el id del usuario del token. Lanza NoAutenticadoError si no es válido o expiró."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITMO],
            options={"require": ["sub", "exp"]},
        )
        if payload.get("tipo") != "acceso":
            raise NoAutenticadoError("Token de sesión inválido.")
        return int(payload["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise NoAutenticadoError("La sesión expiró. Inicia sesión de nuevo.") from exc
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise NoAutenticadoError("Token de sesión inválido.") from exc
