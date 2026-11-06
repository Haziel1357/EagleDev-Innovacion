"""Configuración del registro de eventos (logs)."""

import logging


def configurar_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    # Las librerías de modelos son muy verbosas en DEBUG.
    for ruidoso in ("urllib3", "filelock", "PIL", "httpx", "httpx2"):
        logging.getLogger(ruidoso).setLevel(logging.WARNING)
    # Avisa en cada arranque de que no hay HF_TOKEN; no hace falta para modelos públicos.
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
