"""Constantes compartidas de la aplicación."""

# Roles
ROL_ADMIN = "ADMIN"
ROL_EMPRESA = "EMPRESA"

ROLES_BASE: tuple[tuple[str, str], ...] = (
    (ROL_ADMIN, "Administrador de la plataforma"),
    (ROL_EMPRESA, "Usuario que representa a una empresa o emprendimiento"),
)

# Categorías de material iniciales. El código coincide con las etiquetas del servicio de IA.
CATEGORIAS_BASE: tuple[tuple[str, str, str], ...] = (
    ("madera", "Madera", "Retazos, tablas, aglomerado, MDF, estibas."),
    ("carton", "Cartón", "Cajas, láminas y tubos de cartón."),
    ("plastico", "Plástico", "Envases, láminas, retazos y piezas plásticas."),
    ("tela", "Tela", "Retazos textiles, cuero sintético, lona."),
    ("metal", "Metal", "Láminas, perfiles, tubos, alambre, retal metálico."),
    ("vidrio", "Vidrio", "Láminas, frascos y botellas."),
    ("papel", "Papel", "Hojas, papel kraft, papel de embalaje."),
    ("otro", "Otro", "Materiales que no encajan en otra categoría."),
)

# Actividades económicas iniciales (códigos CIIU rev. 4).
ACTIVIDADES_BASE: tuple[tuple[str, str], ...] = (
    ("1410", "Confección de prendas de vestir"),
    ("1610", "Aserrado, acepillado e impregnación de la madera"),
    ("1690", "Fabricación de otros productos de madera, corcho y cestería"),
    ("1702", "Fabricación de papel y cartón ondulado y envases"),
    ("2229", "Fabricación de artículos de plástico"),
    ("2592", "Tratamiento y revestimiento de metales; mecanizado"),
    ("3110", "Fabricación de muebles"),
    ("3290", "Otras industrias manufactureras (artesanías)"),
    ("3830", "Recuperación de materiales"),
    ("4690", "Comercio al por mayor no especializado"),
)

# Archivos subidos: tipo MIME permitido -> extensión con la que se guarda.
TIPOS_IMAGEN_PERMITIDOS: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_FOTOS_POR_MATERIAL = 6
SUBCARPETA_MATERIALES = "materiales"
SUBCARPETA_RECONOCIMIENTOS = "reconocimientos"

# Reconocimiento con IA: por debajo de esta confianza se pide al usuario que revise.
CONFIANZA_MINIMA_IA = 0.6

# Motor de coincidencias
UMBRAL_COINCIDENCIA = 40.0
"""Puntuación mínima (0-100) para guardar una coincidencia."""

PESOS_COMPATIBILIDAD: dict[str, float] = {
    "material": 0.25,
    "cantidad": 0.20,
    "estado": 0.15,
    "dimensiones": 0.10,
    "ubicacion": 0.15,
    "precio": 0.15,
}
"""Peso de cada criterio en la puntuación de compatibilidad (suman 1)."""

DISTANCIA_IDEAL_KM = 5.0
"""Hasta esta distancia la ubicación puntúa 1."""
DISTANCIA_MAXIMA_KM = 200.0
"""Desde esta distancia la ubicación puntúa 0."""
