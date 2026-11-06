"""Clase base declarativa de la que heredan todos los modelos SQLAlchemy."""

from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import DateTime, MetaData
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Nombres explícitos para índices y restricciones: Alembic los necesita para
# generar migraciones estables (sobre todo al eliminar o renombrar restricciones).
CONVENCION_NOMBRES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def columna_enum(enum: type[Enum]) -> SAEnum:
    """Enum guardado como VARCHAR (no como tipo nativo de PostgreSQL).

    Así añadir un valor nuevo no exige una migración que altere el tipo.
    """
    return SAEnum(enum, native_enum=False, length=30, validate_strings=True)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCION_NOMBRES)


class TimestampMixin:
    """Fechas de creación y de última modificación."""

    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora_utc)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=ahora_utc, onupdate=ahora_utc
    )
