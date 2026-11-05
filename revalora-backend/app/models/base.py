"""Clase base declarativa de la que heredan todos los modelos SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
