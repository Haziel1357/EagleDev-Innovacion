# revalora-ia-service

Servicio de IA de REVALORA (**Python · FastAPI**). Es una aplicación separada del backend.
`revalora-backend` lo llama por HTTP para:

| Ruta | Qué hace | Cómo |
|---|---|---|
| `POST /api/v1/reconocimiento` | Reconoce el material de una foto | Modelo **CLIP** (visión artificial) |
| `POST /api/v1/recomendacion` | Materiales para fabricar un producto descrito en texto | Catálogo de productos + análisis del texto |
| `POST /api/v1/oportunidades` | Productos que se pueden fabricar con ciertos materiales | Catálogo de productos |
| `GET /api/v1/salud` | Comprueba que está activo y qué modelo usa | — |

El formato exacto de peticiones y respuestas está en
[docs/contrato-api-ia.md](../docs/contrato-api-ia.md).

## Requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (instala por sí solo Python 3.12)
- ~1.5 GB libres: dependencias (~800 MB, incluye PyTorch solo-CPU) y el modelo CLIP (~600 MB)
- Internet la **primera vez** para descargar el modelo; después funciona sin conexión
- No hace falta GPU ni base de datos

## Ejecución en desarrollo

```bash
cd revalora-ia-service
uv sync                                         # crea .venv e instala dependencias
cp .env.example .env                            # Windows: copy .env.example .env (opcional)
uv run python -m app.ml.vision.descargar_modelo # descarga CLIP una vez (opcional, ver nota)
uv run uvicorn app.main:app --reload --port 8000
```

- Documentación interactiva (Swagger): http://localhost:8000/docs
- Salud: http://localhost:8000/api/v1/salud → `{"estado":"ok","modelo_vision":"clip"}`

> **Nota:** si no ejecutas `descargar_modelo`, el servicio descarga CLIP al arrancar la
> primera vez, y ese arranque tarda varios minutos. Después carga desde
> `modelos_entrenados/` en unos segundos.

> **Windows:** si dice `uv: command not found`, uv está en `%USERPROFILE%\.local\bin`;
> abre una terminal nueva o añade esa carpeta al PATH.

## Cómo probarlo

### 1. Pruebas automáticas

```bash
uv run pytest                  # todas (~30 s); las que usan CLIP se omiten si no está descargado
uv run pytest -m "not modelo"  # solo las rápidas (~3 s, sin modelo)
uv run pytest -m modelo -v     # solo las que cargan CLIP
uv run ruff check . && uv run ruff format --check .
```

Para medir el reconocimiento con fotos reales, ponlas en `tests/imagenes/` con el nombre
`<material>_<n>.jpg` y ejecuta `uv run pytest -m modelo -v` (ver
[tests/imagenes/README.md](tests/imagenes/README.md)).

### 2. A mano, desde Swagger

Abre http://localhost:8000/docs, elige un endpoint, pulsa **Try it out** y luego **Execute**:

- `/api/v1/reconocimiento`: sube una foto (JPG, PNG o WEBP).
- `/api/v1/recomendacion`: `{"descripcion": "Quiero fabricar marcos para cuadros"}`
- `/api/v1/oportunidades`: `{"materiales": ["madera", "tela"], "max_productos": 5}`

### 3. Con curl

```bash
curl http://localhost:8000/api/v1/salud
curl -X POST http://localhost:8000/api/v1/reconocimiento -F "imagen=@foto.jpg"
curl -X POST http://localhost:8000/api/v1/recomendacion -H "Content-Type: application/json" -d "{\"descripcion\": \"lamparas con botellas\"}"
curl -X POST http://localhost:8000/api/v1/oportunidades -H "Content-Type: application/json" -d "{\"materiales\": [\"madera\"]}"
```

### 4. Junto con el backend

El backend busca este servicio en `IA_SERVICE_URL` (por defecto `http://localhost:8000`).
Si cambias el puerto de la IA, cambia esa variable en el `.env` del backend. Después usa
`POST /api/v1/ia/reconocimiento`, `POST /api/v1/buscador/inteligente` o
`POST /api/v1/oportunidades/analizar` desde el Swagger del backend.

> **Ojo con los puertos:** `uvicorn` sin `--port` usa el **8000**. Si levantas el backend
> así, ocupa el puerto de la IA. Pásale siempre `--port` al backend.

## Configuración (`.env`)

| Variable | Por defecto | Para qué |
|---|---|---|
| `MODELO_VISION` | `auto` | `auto`: CLIP y, si no carga, heurístico. `clip`: solo CLIP (no arranca si falla). `heuristico`: sin modelo. |
| `CLIP_MODELO` | `openai/clip-vit-base-patch32` | Modelo de Hugging Face. |
| `DIRECTORIO_MODELOS` | `modelos_entrenados` | Dónde se guarda el modelo (no se sube a git). |
| `CARGAR_MODELO_AL_INICIAR` | `true` | `false`: arranque inmediato; el modelo se carga con la primera foto. |
| `MAX_PREDICCIONES` | `3` | Alternativas devueltas en `predicciones`. |
| `TAMANO_MAXIMO_IMAGEN_MB` | `5` | Fotos más grandes responden 413. |

## Cómo funciona

### Reconocimiento (`app/ml/vision/`)

- **CLIP en modo *zero-shot*.** El modelo compara la foto con varias descripciones en
  inglés de cada material ("a photo of cardboard boxes", "a photo of rusty iron scrap"…) y
  devuelve la probabilidad de cada uno. No hubo que entrenarlo: `datos/` está vacía. Las
  descripciones están en `app/ml/materiales.py` (`descripciones_clip`).
- **Resultados medidos:** con 21 fotos reales de Wikimedia Commons acertó 20 (95%); el único
  fallo fue una foto antigua en blanco y negro. Las equivocaciones salen con confianza baja
  (< 0.6) y el backend las marca para que el usuario las revise. Tarda ~140 ms por foto en CPU.
- **Clasificador heurístico de respaldo.** Si CLIP no se puede cargar (modo `auto`), se usa
  un clasificador por color y textura para que el servicio no se caiga. **Acierta poco**
  (~15% en la misma prueba); por eso su confianza nunca pasa de 0.5 y el backend marca
  todos sus resultados como "confianza baja". `/api/v1/salud` muestra cuál está en uso.

### Recomendación y oportunidades (`app/ml/recomendacion/`)

- `catalogo_productos.json` tiene 26 productos (marcos, repisas, macetas, lámparas, bolsas…)
  con sus materiales, la función de cada uno, cuál es principal y cantidades estimadas.
- `analizador_producto.py` normaliza el texto (minúsculas, sin tildes, en singular) y busca
  el producto con más palabras clave. También detecta los materiales mencionados ("con
  botellas de vidrio" → vidrio, no plástico).
- `motor_recomendacion.py` calcula la **viabilidad** de cada producto:
  peso de los materiales disponibles / peso total, donde un material principal vale 3 y uno
  secundario vale 1.
- Es un sistema de reglas, no un modelo entrenado: es predecible, se puede probar y se amplía
  editando el JSON.

**Añadir un producto:** edítalo en `catalogo_productos.json` (las instrucciones están al
inicio del archivo) y ejecuta `uv run pytest tests/test_catalogo.py`. Si el JSON tiene un
error, el servicio no arranca y te dice cuál es.

## Estructura

```
revalora-ia-service/
├── pyproject.toml / uv.lock      Dependencias (PyTorch solo-CPU)
├── app/
│   ├── main.py                   Crea la app y carga el modelo al arrancar
│   ├── core/                     Configuración, logging y errores
│   ├── api/
│   │   ├── dependencias.py       Clasificador y motor compartidos
│   │   └── v1/                   router.py + endpoints/ (un archivo por ruta)
│   ├── schemas/                  Esquemas Pydantic (el contrato)
│   ├── services/                 Orquestan validación → modelo → respuesta
│   ├── ml/
│   │   ├── materiales.py         Los 8 materiales: sinónimos y descripciones para CLIP
│   │   ├── vision/               CLIP, heurístico, preprocesamiento y descarga del modelo
│   │   └── recomendacion/        Catálogo, analizador de texto y motor
│   └── utils/                    Validación de imágenes y normalización de texto
├── tests/                        pytest (+ imagenes/ para evaluar con fotos reales)
├── modelos_entrenados/           Modelo descargado (ignorado por git)
├── datos/                        Para entrenar un modelo propio en el futuro (vacía)
├── notebooks/                    Para experimentos (vacía)
└── Dockerfile
```

## Docker

```bash
docker build -t revalora-ia .
docker run -p 8000:8000 -v revalora-modelos:/app/modelos_entrenados revalora-ia
```

El volumen guarda el modelo para no descargarlo en cada arranque.

## Próximos pasos posibles

- **Mejorar el reconocimiento:** juntar fotos propias en `datos/entrenamiento/<material>/` y
  entrenar una capa sobre CLIP (*linear probe*). Con unas decenas de fotos por material
  suele mejorar bastante en fotos de la propia plataforma.
- **Recomendación más flexible:** el catálogo solo reconoce productos que tiene. Para
  descripciones libres se podría usar un modelo de lenguaje, manteniendo el mismo contrato.
