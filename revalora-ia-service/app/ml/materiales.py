"""Materiales que reconoce el servicio.

Los códigos deben coincidir con ``categorias_material.codigo`` del backend
(``revalora-backend/app/utils/constantes.py``, CATEGORIAS_BASE): en minúsculas y sin tildes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    codigo: str
    nombre: str
    # Palabras o frases en singular que, si aparecen en un texto, indican este material.
    # Se usan en el analizador de productos (que normaliza tildes y mayúsculas).
    sinonimos: tuple[str, ...]
    # Descripciones en inglés para CLIP (entiende inglés mucho mejor que español).
    # Se promedian varias por material para que el resultado sea más estable.
    descripciones_clip: tuple[str, ...]


MATERIALES: tuple[Material, ...] = (
    Material(
        codigo="madera",
        nombre="Madera",
        sinonimos=(
            "madera",
            "pino",
            "roble",
            "cedro",
            "mdf",
            "aglomerado",
            "triplex",
            "triplay",
            "contrachapado",
            "estiba",
            "palet",
            "pallet",
            "tabla",
            "tablon",
            "liston",
            "viruta",
            "aserrin",
            "melamina",
            "bambu",
        ),
        descripciones_clip=(
            "a photo of wood",
            "a photo of wooden planks",
            "a photo of scrap wood pieces",
            "a photo of a wooden pallet",
            "a photo of plywood or MDF boards",
        ),
    ),
    Material(
        codigo="carton",
        nombre="Cartón",
        sinonimos=("carton", "corrugado", "caja de carton", "cartulina", "tubo de carton"),
        descripciones_clip=(
            "a photo of cardboard",
            "a photo of cardboard boxes",
            "a photo of corrugated cardboard",
            "a photo of flattened cardboard sheets",
        ),
    ),
    Material(
        codigo="plastico",
        nombre="Plástico",
        sinonimos=(
            "plastico",
            "pet",
            "pvc",
            "polietileno",
            "polipropileno",
            "acrilico",
            "botella",
            "envase",
            "tapa",
            "tapita",
            "bolsa plastica",
            "icopor",
            "poliestireno",
        ),
        descripciones_clip=(
            "a photo of plastic",
            "a photo of plastic bottles",
            "a photo of plastic containers",
            "a photo of plastic waste",
            "a photo of plastic sheets",
        ),
    ),
    Material(
        codigo="tela",
        nombre="Tela",
        sinonimos=(
            # "retazo" no se incluye: se usa con cualquier material ("retazos de MDF").
            "tela",
            "textil",
            "algodon",
            "lona",
            "jean",
            "mezclilla",
            "denim",
            "lana",
            "poliester",
            "cuero",
            "fieltro",
            "seda",
            "lino",
            "hilo",
            "ropa",
        ),
        descripciones_clip=(
            "a photo of fabric",
            "a photo of fabric scraps",
            "a photo of textile",
            "a photo of folded cloth",
            "a photo of denim or canvas fabric",
        ),
    ),
    Material(
        codigo="metal",
        nombre="Metal",
        sinonimos=(
            "metal",
            "metalico",
            "aluminio",
            "acero",
            "hierro",
            "cobre",
            "bronce",
            "lata",
            "alambre",
            "chatarra",
            "lamina metalica",
            "tubo metalico",
            "perfil",
            "tornillo",
            "clavo",
            "varilla",
        ),
        descripciones_clip=(
            "a photo of metal",
            "a photo of scrap metal",
            "a photo of metal sheets",
            "a photo of metal pipes and rods",
            "a photo of aluminum cans",
            "a photo of rusty metal plates",
            "a photo of rusty iron scrap",
        ),
    ),
    Material(
        codigo="vidrio",
        nombre="Vidrio",
        sinonimos=("vidrio", "cristal", "frasco", "botella de vidrio", "espejo", "vitral"),
        descripciones_clip=(
            "a photo of glass",
            "a photo of glass bottles",
            "a photo of glass jars",
            "a photo of a glass sheet",
            "a photo of broken glass",
            "a photo of brown glass beer bottles",
            "a photo of green glass bottles",
        ),
    ),
    Material(
        codigo="papel",
        nombre="Papel",
        sinonimos=(
            "papel",
            "hoja",
            "periodico",
            "revista",
            "kraft",
            "papel kraft",
            "cuaderno",
            "folleto",
            "papel de embalaje",
        ),
        descripciones_clip=(
            "a photo of paper",
            "a photo of stacked paper sheets",
            "a photo of newspapers",
            "a photo of crumpled paper",
            "a photo of kraft paper",
        ),
    ),
    Material(
        codigo="otro",
        nombre="Otro",
        sinonimos=(),
        descripciones_clip=(
            "a photo of an object",
            "a photo of rubber",
            "a photo of stone or ceramic",
            "a photo of foam",
            "a photo of electronic waste",
        ),
    ),
)

CODIGOS_MATERIAL: frozenset[str] = frozenset(m.codigo for m in MATERIALES)
MATERIAL_POR_CODIGO: dict[str, Material] = {m.codigo: m for m in MATERIALES}

# Unidades de medida aceptadas por el backend (UnidadMedida).
UNIDADES: frozenset[str] = frozenset(
    {"UNIDAD", "KILOGRAMO", "METRO", "METRO_CUADRADO", "METRO_CUBICO", "LITRO"}
)
