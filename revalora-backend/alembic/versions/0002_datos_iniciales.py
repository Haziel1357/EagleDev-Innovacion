"""datos iniciales: roles, categorías de material y actividades económicas

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04 21:45:00

Los valores están escritos aquí (no importados de app.utils.constantes) para que la
migración siga dando el mismo resultado aunque las constantes cambien más adelante.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROLES = [
    {"nombre": "ADMIN", "descripcion": "Administrador de la plataforma"},
    {"nombre": "EMPRESA", "descripcion": "Usuario que representa a una empresa o emprendimiento"},
]

CATEGORIAS = [
    {
        "codigo": "madera",
        "nombre": "Madera",
        "descripcion": "Retazos, tablas, aglomerado, MDF, estibas.",
    },
    {"codigo": "carton", "nombre": "Cartón", "descripcion": "Cajas, láminas y tubos de cartón."},
    {
        "codigo": "plastico",
        "nombre": "Plástico",
        "descripcion": "Envases, láminas, retazos y piezas plásticas.",
    },
    {"codigo": "tela", "nombre": "Tela", "descripcion": "Retazos textiles, cuero sintético, lona."},
    {
        "codigo": "metal",
        "nombre": "Metal",
        "descripcion": "Láminas, perfiles, tubos, alambre, retal metálico.",
    },
    {"codigo": "vidrio", "nombre": "Vidrio", "descripcion": "Láminas, frascos y botellas."},
    {"codigo": "papel", "nombre": "Papel", "descripcion": "Hojas, papel kraft, papel de embalaje."},
    {
        "codigo": "otro",
        "nombre": "Otro",
        "descripcion": "Materiales que no encajan en otra categoría.",
    },
]

ACTIVIDADES = [
    {"codigo": "1410", "nombre": "Confección de prendas de vestir"},
    {"codigo": "1610", "nombre": "Aserrado, acepillado e impregnación de la madera"},
    {"codigo": "1690", "nombre": "Fabricación de otros productos de madera, corcho y cestería"},
    {"codigo": "1702", "nombre": "Fabricación de papel y cartón ondulado y envases"},
    {"codigo": "2229", "nombre": "Fabricación de artículos de plástico"},
    {"codigo": "2592", "nombre": "Tratamiento y revestimiento de metales; mecanizado"},
    {"codigo": "3110", "nombre": "Fabricación de muebles"},
    {"codigo": "3290", "nombre": "Otras industrias manufactureras (artesanías)"},
    {"codigo": "3830", "nombre": "Recuperación de materiales"},
    {"codigo": "4690", "nombre": "Comercio al por mayor no especializado"},
]

roles = sa.table("roles", sa.column("nombre", sa.String), sa.column("descripcion", sa.String))
categorias = sa.table(
    "categorias_material",
    sa.column("codigo", sa.String),
    sa.column("nombre", sa.String),
    sa.column("descripcion", sa.String),
    sa.column("activa", sa.Boolean),
)
actividades = sa.table(
    "actividades_economicas", sa.column("codigo", sa.String), sa.column("nombre", sa.String)
)


def upgrade() -> None:
    op.bulk_insert(roles, ROLES)
    op.bulk_insert(categorias, [{**c, "activa": True} for c in CATEGORIAS])
    op.bulk_insert(actividades, ACTIVIDADES)


def downgrade() -> None:
    op.execute(
        actividades.delete().where(actividades.c.codigo.in_([a["codigo"] for a in ACTIVIDADES]))
    )
    op.execute(
        categorias.delete().where(categorias.c.codigo.in_([c["codigo"] for c in CATEGORIAS]))
    )
    op.execute(roles.delete().where(roles.c.nombre.in_([r["nombre"] for r in ROLES])))
