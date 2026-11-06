# Imagen del servicio de IA de REVALORA.
#
#   docker build -t revalora-ia .
#   docker run -p 8000:8000 -v revalora-modelos:/app/modelos_entrenados revalora-ia
#
# El volumen guarda el modelo CLIP (~600 MB) para no descargarlo en cada arranque.

FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Primero solo las dependencias, para aprovechar la caché de Docker.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
