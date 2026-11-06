"""Clasificadores de materiales a partir de una foto.

Hay dos implementaciones con la misma interfaz (``clasificar``):

- ``ClasificadorClip``: usa CLIP (openai/clip-vit-base-patch32) en modo *zero-shot*: compara
  la foto con descripciones de texto de cada material ("a photo of cardboard boxes"...)
  y elige la más parecida. No necesita entrenamiento ni fotos propias.
- ``ClasificadorHeuristico``: respaldo sin modelo, basado en color y textura. Es rápido y no
  descarga nada, pero acierta poco; por eso su confianza nunca supera ``CONFIANZA_MAXIMA``
  (el backend marca como "confianza baja" todo lo que esté por debajo de 0.6).

``crear_clasificador`` elige cuál usar según ``MODELO_VISION``.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from PIL import Image

from app.core.config import Settings
from app.core.errores import ModeloNoDisponibleError
from app.ml.materiales import MATERIALES

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Prediccion:
    material: str
    confianza: float


class ClasificadorMateriales(Protocol):
    nombre: str

    def clasificar(self, imagen: Image.Image) -> list[Prediccion]:
        """Predicciones para todos los materiales, ordenadas de mayor a menor confianza.
        Las confianzas suman 1."""
        ...


def _ordenar(codigos: list[str], probabilidades: np.ndarray) -> list[Prediccion]:
    pares = zip(codigos, probabilidades.tolist(), strict=True)
    return sorted(
        (Prediccion(codigo, float(p)) for codigo, p in pares),
        key=lambda p: p.confianza,
        reverse=True,
    )


def _softmax(valores: np.ndarray) -> np.ndarray:
    exp = np.exp(valores - valores.max())
    return exp / exp.sum()


# ------------------------------------------------------------------------------- CLIP


class ClasificadorClip:
    nombre = "clip"

    def __init__(self, modelo: str, directorio_cache: str | None = None) -> None:
        # Importación diferida: torch tarda varios segundos en cargar y el modo
        # heurístico (y las pruebas) no lo necesitan.
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self._torch = torch
        logger.info("Cargando modelo de visión %s ...", modelo)
        try:
            # Primero desde disco: arranca más rápido y funciona sin internet.
            self._cargar(CLIPModel, CLIPProcessor, modelo, directorio_cache, solo_local=True)
        except OSError:
            logger.info("El modelo no está en %s; descargándolo (~600 MB)...", directorio_cache)
            self._cargar(CLIPModel, CLIPProcessor, modelo, directorio_cache, solo_local=False)
        self._codigos = [m.codigo for m in MATERIALES]
        self._textos = self._embeddings_de_texto()
        self._lock = threading.Lock()
        logger.info("Modelo de visión listo.")

    def _cargar(self, clase_modelo, clase_procesador, modelo, cache, solo_local: bool) -> None:
        opciones = {"cache_dir": cache, "local_files_only": solo_local}
        # use_safetensors: descarga una sola copia de los pesos (~600 MB en vez de ~1.2 GB) en
        # el formato seguro (el .bin usa pickle, que puede ejecutar código al cargarse).
        self._modelo = clase_modelo.from_pretrained(modelo, use_safetensors=True, **opciones).eval()
        self._procesador = clase_procesador.from_pretrained(modelo, **opciones)

    @staticmethod
    def _vector(salida):
        # transformers 5 devuelve un objeto con el vector en pooler_output; la 4, el tensor.
        return getattr(salida, "pooler_output", salida)

    def _embeddings_de_texto(self):
        """Un vector por material: el promedio de los vectores de sus descripciones."""
        torch = self._torch
        vectores = []
        with torch.inference_mode():
            for material in MATERIALES:
                entradas = self._procesador(
                    text=list(material.descripciones_clip), return_tensors="pt", padding=True
                )
                texto = self._vector(self._modelo.get_text_features(**entradas))
                texto = texto / texto.norm(dim=-1, keepdim=True)
                media = texto.mean(dim=0)
                vectores.append(media / media.norm())
        return torch.stack(vectores)

    def clasificar(self, imagen: Image.Image) -> list[Prediccion]:
        torch = self._torch
        with self._lock, torch.inference_mode():
            entradas = self._procesador(images=imagen, return_tensors="pt")
            vector = self._vector(self._modelo.get_image_features(**entradas))
            vector = vector / vector.norm(dim=-1, keepdim=True)
            escala = self._modelo.logit_scale.exp()
            logits = (escala * vector @ self._textos.T)[0]
            probabilidades = logits.softmax(dim=-1).cpu().numpy()
        return _ordenar(self._codigos, probabilidades)


# ------------------------------------------------------------------------- Heurístico


class ClasificadorHeuristico:
    """Reglas de color y textura. Ejemplos: tonos marrones con vetas → madera;
    marrón claro y liso → cartón; blanco y liso → papel; colores saturados → plástico."""

    nombre = "heuristico"
    CONFIANZA_MAXIMA = 0.5

    def clasificar(self, imagen: Image.Image) -> list[Prediccion]:
        rasgos = self._rasgos(imagen)
        puntajes = {
            "madera": 2.0 * rasgos["marron"] + 1.0 * rasgos["textura"],
            "carton": 2.0 * rasgos["marron"] + 1.0 * (1 - rasgos["textura"]) * rasgos["brillo"],
            "papel": 1.5 * (1 - rasgos["saturacion"]) * rasgos["brillo"]
            + 0.5 * (1 - rasgos["textura"]),
            "plastico": 2.0 * rasgos["saturacion"] * (1 - rasgos["marron"]),
            "tela": 1.5 * rasgos["textura"] * (1 - rasgos["marron"]) + 0.3 * rasgos["saturacion"],
            "metal": 1.5 * (1 - rasgos["saturacion"]) * rasgos["contraste"],
            "vidrio": 1.0 * (1 - rasgos["saturacion"]) * rasgos["brillo"] * rasgos["contraste"],
            "otro": 0.4,
        }
        codigos = [m.codigo for m in MATERIALES]
        probabilidades = _softmax(np.array([puntajes[c] for c in codigos]) * 2.0)
        return _ordenar(codigos, self._limitar(probabilidades))

    @classmethod
    def _limitar(cls, probabilidades: np.ndarray) -> np.ndarray:
        """Baja la confianza máxima a CONFIANZA_MAXIMA y reparte el resto en proporción.
        Es una estimación aproximada, no un modelo entrenado."""
        mayor = int(probabilidades.argmax())
        if probabilidades[mayor] <= cls.CONFIANZA_MAXIMA:
            return probabilidades
        otros = probabilidades.copy()
        otros[mayor] = 0.0
        total_otros = otros.sum()
        if total_otros > 0:
            otros = otros / total_otros * (1 - cls.CONFIANZA_MAXIMA)
        else:
            otros[:] = (1 - cls.CONFIANZA_MAXIMA) / (len(otros) - 1)
            otros[mayor] = 0.0
        otros[mayor] = cls.CONFIANZA_MAXIMA
        return otros

    @staticmethod
    def _rasgos(imagen: Image.Image) -> dict[str, float]:
        """Rasgos entre 0 y 1: proporción de píxeles marrones, saturación, brillo,
        contraste y textura (densidad de bordes)."""
        pequena = imagen.resize((128, 128))
        hsv = np.asarray(pequena.convert("HSV"), dtype=np.float32) / 255.0
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        gris = np.asarray(pequena.convert("L"), dtype=np.float32) / 255.0

        marron = (h > 0.03) & (h < 0.12) & (s > 0.2) & (s < 0.8) & (v > 0.15) & (v < 0.85)
        bordes = np.abs(np.diff(gris, axis=0)).mean() + np.abs(np.diff(gris, axis=1)).mean()
        return {
            "marron": float(marron.mean()),
            "saturacion": float(s.mean()),
            "brillo": float(v.mean()),
            "contraste": float(min(gris.std() * 3, 1.0)),
            "textura": float(min(bordes * 8, 1.0)),
        }


# ------------------------------------------------------------------------------ Fábrica


def crear_clasificador(config: Settings) -> ClasificadorMateriales:
    """Crea el clasificador indicado en MODELO_VISION.

    En modo ``auto`` intenta CLIP y, si falla (sin internet la primera vez, sin memoria...),
    usa el heurístico y lo deja anotado en el log.
    """
    if config.modelo_vision == "heuristico":
        return ClasificadorHeuristico()
    try:
        config.ruta_modelos.mkdir(parents=True, exist_ok=True)
        return ClasificadorClip(config.clip_modelo, str(config.ruta_modelos))
    except Exception as exc:
        if config.modelo_vision == "clip":
            raise ModeloNoDisponibleError(
                f"No se pudo cargar el modelo de visión {config.clip_modelo}: {exc}"
            ) from exc
        logger.warning(
            "No se pudo cargar CLIP (%s). Se usará el clasificador heurístico, que es poco "
            "preciso. Revisa la conexión o ejecuta: uv run python -m app.ml.vision.descargar_modelo",
            exc,
        )
        return ClasificadorHeuristico()


class ProveedorClasificador:
    """Crea el clasificador una sola vez (al arrancar o con la primera foto) y lo comparte."""

    def __init__(self, config: Settings) -> None:
        self._config = config
        self._clasificador: ClasificadorMateriales | None = None
        self._lock = threading.Lock()

    @property
    def nombre(self) -> str:
        return self._clasificador.nombre if self._clasificador else "sin_cargar"

    def obtener(self) -> ClasificadorMateriales:
        if self._clasificador is None:
            with self._lock:
                if self._clasificador is None:
                    self._clasificador = crear_clasificador(self._config)
        return self._clasificador
