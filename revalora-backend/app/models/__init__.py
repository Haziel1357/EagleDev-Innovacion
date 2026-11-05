"""Modelos SQLAlchemy de REVALORA.

Importa aquí cada modelo a medida que se implemente, para que Alembic los
detecte al generar migraciones (alembic revision --autogenerate).
"""

from app.models.base import Base

__all__ = ["Base"]
