"""Normalización de texto en español para comparar palabras clave.

"Quiero fabricar Lámparas" y "lampara" deben coincidir, así que se pasa a minúsculas,
se quitan tildes y signos, se descartan palabras vacías y se generan las formas
singulares posibles de cada palabra.
"""

import re
import unicodedata

PALABRAS_VACIAS = frozenset(
    {
        "a",
        "al",
        "algo",
        "algun",
        "alguna",
        "con",
        "de",
        "del",
        "el",
        "en",
        "es",
        "esta",
        "este",
        "hacer",
        "fabricar",
        "elaborar",
        "crear",
        "producir",
        "construir",
        "la",
        "las",
        "lo",
        "los",
        "me",
        "mi",
        "mis",
        "necesito",
        "o",
        "para",
        "por",
        "que",
        "quiero",
        "quisiera",
        "se",
        "sin",
        "su",
        "sus",
        "tipo",
        "u",
        "un",
        "una",
        "unas",
        "unos",
        "y",
        "como",
        "tengo",
        "usar",
        "utilizar",
        "reciclar",
        "reutilizar",
    }
)

_NO_ALFANUMERICO = re.compile(r"[^a-z0-9]+")


def quitar_tildes(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def palabras(texto: str) -> list[str]:
    """Palabras significativas del texto: minúsculas, sin tildes ni signos ni palabras vacías."""
    limpio = _NO_ALFANUMERICO.sub(" ", quitar_tildes(texto.lower()))
    return [p for p in limpio.split() if p not in PALABRAS_VACIAS]


def formas_singulares(palabra: str) -> set[str]:
    """Formas posibles de una palabra en singular.

    No es un lematizador completo; cubre los plurales regulares del español:
    marcos→marco, cojines→cojin, lapices→lapiz, estantes→estante.
    """
    formas = {palabra}
    if len(palabra) > 3 and palabra.endswith("s"):
        formas.add(palabra[:-1])
        if palabra.endswith("es"):
            formas.add(palabra[:-2])
            if palabra.endswith("ces"):
                formas.add(palabra[:-3] + "z")
    return formas


def vocabulario(texto: str) -> set[str]:
    """Todas las formas (originales y singulares) de las palabras del texto."""
    resultado: set[str] = set()
    for palabra in palabras(texto):
        resultado |= formas_singulares(palabra)
    return resultado


def clave(frase: str) -> frozenset[str]:
    """Palabras de una palabra clave o frase clave, normalizadas."""
    return frozenset(palabras(frase))


def contiene(vocab: set[str], frase_clave: frozenset[str]) -> bool:
    """True si todas las palabras de la frase clave aparecen en el vocabulario del texto."""
    return bool(frase_clave) and frase_clave <= vocab
