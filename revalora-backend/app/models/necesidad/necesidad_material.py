"""Entidad NecesidadMaterial: material que una empresa necesita (cantidad, estado mínimo y presupuesto)."""

from decimal import Decimal

from sqlalchemy import Float, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

from app.models.base import Base, TimestampMixin, columna_enum
from app.models.empresa.empresa import Empresa
from app.models.material.categoria_material import CategoriaMaterial
from app.models.material.dimensiones import Dimensiones
from app.models.material.enums import EstadoMaterial, UnidadMedida
from app.models.necesidad.enums import EstadoNecesidad


class NecesidadMaterial(TimestampMixin, Base):
    __tablename__ = "necesidades_material"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresas.id"), index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias_material.id"), index=True)
    titulo: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text)
    cantidad: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unidad_medida: Mapped[UnidadMedida] = mapped_column(columna_enum(UnidadMedida))
    estado_minimo: Mapped[EstadoMaterial] = mapped_column(
        columna_enum(EstadoMaterial), default=EstadoMaterial.REGULAR
    )
    presupuesto_maximo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estado: Mapped[EstadoNecesidad] = mapped_column(
        columna_enum(EstadoNecesidad), default=EstadoNecesidad.ABIERTA, index=True
    )

    # Medidas mínimas que debe tener el material (opcionales).
    largo_min_cm: Mapped[float | None] = mapped_column(Float)
    ancho_min_cm: Mapped[float | None] = mapped_column(Float)
    alto_min_cm: Mapped[float | None] = mapped_column(Float)
    dimensiones_minimas: Mapped[Dimensiones] = composite(
        Dimensiones, "largo_min_cm", "ancho_min_cm", "alto_min_cm"
    )

    empresa: Mapped[Empresa] = relationship(lazy="joined")
    categoria: Mapped[CategoriaMaterial] = relationship(lazy="joined")
