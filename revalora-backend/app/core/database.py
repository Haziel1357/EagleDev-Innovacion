"""Conexión a PostgreSQL con SQLAlchemy y dependencia de sesión para FastAPI."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Abre una sesión por petición y la cierra al terminar.

    Los servicios confirman con ``db.commit()``; si la petición falla antes, los
    cambios pendientes se descartan al cerrar la sesión.
    """
    with SessionLocal() as db:
        yield db


DbSession = Annotated[Session, Depends(get_db)]
