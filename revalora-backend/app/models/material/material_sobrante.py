"""Entidad MaterialSobrante: material publicado para venta, intercambio o aprovechamiento."""

from decimal import Decimal

from sqlalchemy import Boolean, Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.empresa.empresa import Empresa
from app.models.material.categoria_material import CategoriaMaterial
from app.models.material.dimensiones import Dimensiones
from app.models.material.enums import (
    DisponibilidadMaterial,
    EstadoMaterial,
    TipoOferta,
    UnidadMedida,
)
from app.models.material.foto_material import FotoMaterial


class MaterialSobrante(TimestampMixin, Base):
    __tablename__ = "materiales_sobrantes"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias_material.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unidad_medida: Mapped[UnidadMedida] = mapped_column(columna_enum(UnidadMedida))
    estado: Mapped[EstadoMaterial] = mapped_column(columna_enum(EstadoMaterial))
    tipo_oferta: Mapped[TipoOferta] = mapped_column(columna_enum(TipoOferta))
    precio: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    disponibilidad: Mapped[DisponibilidadMaterial] = mapped_column(
        columna_enum(DisponibilidadMaterial),
        default=DisponibilidadMaterial.DISPONIBLE,
        index=True,
    )
    # True cuando la IA reconoció el material de la foto y el usuario lo confirmó.
    verificado_ia: Mapped[bool] = mapped_column(Boolean, default=False)

    largo_cm: Mapped[float | None] = mapped_column(Float)
    ancho_cm: Mapped[float | None] = mapped_column(Float)
    alto_cm: Mapped[float | None] = mapped_column(Float)
    dimensiones: Mapped[Dimensiones] = composite(Dimensiones, "largo_cm", "ancho_cm", "alto_cm")

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    categoria: Mapped[CategoriaMaterial] = relationship(lazy="joined")
    fotos: Mapped[list[FotoMaterial]] = relationship(
        back_populates="material",
        cascade="all, delete-orphan",
        order_by=(FotoMaterial.es_principal.desc(), FotoMaterial.id),
        lazy="selectin",
    )

    @property
    def esta_disponible(self) -> bool:
        return self.disponibilidad == DisponibilidadMaterial.DISPONIBLE
