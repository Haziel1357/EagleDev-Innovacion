"""Entidad Usuario: cuenta de acceso a la plataforma."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.usuario.rol import Rol

if TYPE_CHECKING:
    from app.models.empresa.empresa import Empresa


class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

    rol: Mapped[Rol] = relationship(lazy="joined")
    empresa: Mapped["Empresa | None"] = relationship(back_populates="usuario", uselist=False)

    @property
    def rol_nombre(self) -> str:
        return self.rol.nombre

    @property
    def empresa_id(self) -> int | None:
        return self.empresa.id if self.empresa else None

    @property
    def es_admin(self) -> bool:
        from app.utils.constantes import ROL_ADMIN

        return self.rol.nombre == ROL_ADMIN
