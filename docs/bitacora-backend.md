# Bitácora del backend

Registro de lo que se ha hecho en `revalora-backend` y por qué. Léelo antes de empezar a
trabajar en el backend o en la API. Para saber *cómo* trabajar en la API, ve a
[guia-api.md](guia-api.md).

Última actualización: 2026-11-05 (rama `Api`).

## Resumen del estado actual

| Parte | Estado |
|---|---|
| API REST del backend (`revalora-backend`, `/api/v1`) | Hecha: 9 módulos y 53 rutas, con 84 pruebas que pasan. |
| Migraciones de base de datos (Alembic) | Escritas (`0001`, `0002`), **sin probar todavía contra un PostgreSQL real**. |
| Vistas web (Jinja2, CSS, JS) | **Por hacer.** Solo `layout/base.html` y `home/index.html` tienen contenido; el resto de plantillas, CSS y JS son archivos vacíos. |
| Servicio de IA (`revalora-ia-service`) | Hecho: reconocimiento con CLIP, recomendación y oportunidades, con 50 pruebas. Probado de punta a punta con el backend. Ver la sección 5. |

## Cronología

### 1. Estructura inicial — Haziel1357 (2026-11-03)

Commits `62a73bc` y `c1bcf1f`. Estructura del proyecto con el backend en **Java / Spring
Boot** y la descripción del proyecto en el README.

### 2. Migración de Spring Boot a FastAPI — CuBe533 (2026-11-04)

Commit `983a109`. Se eliminó el proyecto Java (Maven) y se creó el esqueleto en Python
manteniendo la misma organización por capas y módulos:

- `core/` (configuración, base de datos, logging, plantillas), `exceptions/` (errores de
  negocio y manejadores globales) y `main.py` quedaron funcionales.
- Controladores, modelos y servicios quedaron como archivos casi vacíos.
- En `revalora-backend/README.md` hay una tabla de equivalencias Spring Boot → Python.

### 3. Implementación de la API — diego281010 (2026-11-04)

Commit `02cf8ae`. Es el grueso del trabajo (unas 8.900 líneas):

- **Dependencias con uv**: `pyproject.toml` + `uv.lock` + `.python-version` (Python 3.12)
  en lugar de `requirements.txt`.
- **Los 9 módulos completos**: usuario, empresa, material, necesidad, ia, buscador,
  coincidencia, transaccion y oportunidad. Cada uno tiene modelo, esquema, repositorio,
  servicio y controlador.
- **Seguridad**: JWT (cabecera `Authorization: Bearer` o cookie `access_token`) y
  contraseñas con Argon2.
- **Lógica de negocio**: motor de coincidencias con puntuación 0-100, buscador
  inteligente y tradicional, solicitudes con historial, y oportunidades productivas.
- **Cliente del servicio de IA** (`app/services/ia/ia_service_client.py`) y su contrato
  en `docs/contrato-api-ia.md`.
- **Migraciones** `0001_esquema_inicial` (tablas) y `0002_datos_iniciales` (roles,
  categorías y actividades económicas).
- **74 pruebas** con SQLite en memoria y una IA simulada.

### 4. Orden de la API y separación de las vistas — rama `Api` (2026-11-05)

Revisión de la API, que se va a seguir desarrollando de forma independiente a las vistas.

**Cambio principal: la API se separó de las páginas web.**

- *Problema:* los controladores de JSON estaban en la raíz (`GET /materiales` devolvía
  JSON). Cuando se hicieran las páginas HTML, `/materiales` no podría ser a la vez la
  página y el endpoint.
- *Solución:*
  - `app/controllers/api/<modulo>/`: endpoints JSON, todos bajo **`/api/v1`**.
  - `app/controllers/web/<modulo>/`: páginas HTML que renderizan `templates/`.
  - El prefijo está en una sola constante: `PREFIJO_API` en `app/core/config.py`.
- *Consecuencias:*
  - Todas las rutas de la API cambiaron de `/x` a `/api/v1/x`. Por ejemplo, `/salud`
    pasó a ser `/api/v1/salud`.
  - Swagger (`/docs`) obtiene el token en `/api/v1/auth/token`.
  - Bajo `/api/v1` los errores responden **siempre en JSON**, aunque la petición venga de
    un navegador. Antes un 404 de la API pedido desde el navegador devolvía HTML.
- Los archivos se movieron con `git mv`, así que el historial de cada uno se conserva
  (`git log --follow`).

**Bug corregido.** `PUT /api/v1/necesidades/{id}` devolvía la categoría anterior cuando se
cambiaba `categoria_id`. En la base de datos sí se guardaba bien; solo fallaba la
respuesta, porque la relación en memoria no se recargaba. Se añadió `db.refresh()` en
`NecesidadMaterialService.actualizar`, igual que ya hacía el servicio de materiales.

**Pruebas reorganizadas por capa.**

- Las pruebas de buscador y de reconocimiento IA estaban en `tests/services/` pero
  prueban por HTTP, así que se movieron a `tests/controllers/api/`.
- El archivo de coincidencias se dividió en dos:
  - `tests/services/coincidencia/test_puntuacion_compatibilidad_service.py`: cálculo puro.
  - `tests/controllers/api/coincidencia/test_coincidencia_controller.py`: rutas.
- Nuevas pruebas para necesidades (el único módulo que no tenía ninguna). La de
  actualización es la que encontró el bug.
- Dos pruebas nuevas en `tests/test_main.py`: una comprueba que toda ruta del OpenAPI
  empieza por `/api/v1/` y otra que los errores de la API responden en JSON.
- Total: 74 → 84 pruebas.

**Limpieza de carpetas.**

- Se eliminaron 18 carpetas de `tests/` que solo tenían un `.gitkeep` (andamiaje sin
  pruebas) y el `.gitkeep` sobrante de `alembic/versions/`.
- Si se escriben pruebas para un módulo nuevo, se crea su carpeta en ese momento.
- Se conservan `uploads/.gitkeep` y los `.gitkeep` de `app/static/img/`, porque esas
  carpetas tienen que existir.
- Se actualizaron `README.md`, `revalora-backend/README.md` y `ESTRUCTURA.txt`.

### 5. Servicio de IA — rama `Api` (2026-11-05)

`revalora-ia-service` tenía la estructura de carpetas pero sus 41 archivos estaban vacíos.
Se implementó completo, cumpliendo [contrato-api-ia.md](contrato-api-ia.md). El detalle
está en `revalora-ia-service/README.md`.

- **Dependencias con uv**, como el backend: `pyproject.toml` + `uv.lock` + Python 3.12. Se
  eliminó `requirements.txt`. PyTorch se instala en su versión solo-CPU para que Docker no
  descargue ~2 GB de CUDA.
- **Reconocimiento de fotos**: modelo CLIP (`openai/clip-vit-base-patch32`) en modo
  *zero-shot*: compara la foto con descripciones de cada material, sin entrenamiento propio
  (`datos/` sigue vacía).
  - El modelo pesa ~600 MB y se guarda en `modelos_entrenados/`, que está en `.gitignore`.
  - Se descarga solo en formato *safetensors*, para no bajar dos copias de los pesos.
  - Hay un clasificador heurístico de respaldo (color y textura). Acierta poco, así que su
    confianza nunca pasa de 0.5 y el backend lo marca como "confianza baja".
- **Recomendación y oportunidades**:
  - Catálogo de 26 productos en `app/ml/recomendacion/catalogo_productos.json`, que se
    valida al arrancar.
  - Análisis del texto en español: tildes, plurales y materiales mencionados.
  - La viabilidad pondera los materiales: principal = 3, secundario = 1.
  - Es un sistema de reglas, no un modelo entrenado.
- **Errores** con el mismo formato JSON que el backend: 400 si la imagen no es válida, 413
  si es demasiado grande, 422 si los datos son inválidos y 503 si no hay modelo.

**Cómo se comprobó:**

- 50 pruebas automáticas que no necesitan el modelo, más pruebas con CLIP real (marca
  `modelo`). Ruff sin errores.
- **Precisión con fotos reales**: 21 fotos de Wikimedia Commons, 20 aciertos (95%). El único
  fallo fue una foto antigua en blanco y negro.
  - Se descartaron 6 fotos de la búsqueda que no eran del material (una flor, un termómetro…).
  - Se añadieron descripciones para metal oxidado y vidrio de color después de ver dos de
    esas fotos, así que la cifra es algo optimista: con fotos claras se puede esperar entre
    el 86% y el 95%.
  - ~140 ms por foto en CPU.
  - Las fotos no se subieron por sus licencias. `tests/imagenes/` está preparada para que el
    equipo ponga fotos propias.
- **De punta a punta**: los dos servicios levantados y conectados (backend con SQLite
  temporal). Se probó registro → empresa → foto de botellas (vidrio, 97.6%) → material
  publicado con `verificado_ia: true` → buscador "lámparas para restaurantes" →
  oportunidades. Todo respondió correctamente.

**Puertos en el equipo de desarrollo (Windows):** el 8080 lo ocupa `AgentService.exe`, un
servicio del sistema, y `uvicorn` sin `--port` usa el 8000, que es el de la IA. Levanta el
backend con un puerto explícito libre (por ejemplo `--port 8081`).

## Cómo se comprobó que funciona

1. `uv run pytest`: 84 pruebas pasan. Usan SQLite en memoria y una IA falsa, así que no
   necesitan PostgreSQL ni el servicio de IA.
2. `uv run ruff check .` y `uv run ruff format --check .`: sin errores.
3. Se levantó el servidor (`uvicorn`) y se probó a mano:
   - `GET /api/v1/salud` responde `{"estado":"ok"}`.
   - `GET /salud` (la ruta vieja) responde 404.
   - `GET /` devuelve la página HTML.
   - Un 404 bajo `/api/v1` pedido como navegador responde en JSON.
   - El OpenAPI tiene 53 rutas, todas con `/api/v1`, y Swagger usa `/api/v1/auth/token`.

**Lo que todavía no se ha comprobado:**

- `uv run alembic upgrade head` contra un PostgreSQL real.
- Las rutas que dependen del servicio de IA, cuando se hizo esta revisión. Se comprobaron
  después, en la sección 5.

## Pendientes

1. **Mejorar la IA** (opcional):
   - Reunir fotos propias en `datos/entrenamiento/<material>/` y entrenar una capa sobre
     CLIP.
   - Ampliar `catalogo_productos.json` con más productos.
2. **Probar las migraciones** con PostgreSQL: crear `.env` a partir de `.env.example`,
   ejecutar `uv run alembic upgrade head` y después `uv run alembic check`.
3. **Vistas web**: controladores en `app/controllers/web/<modulo>/` y plantillas.
   `static/js/api-client.js` debe llamar a la API con el prefijo `/api/v1`.
4. **Documentos vacíos** en `docs/`: `arquitectura.md`, `modelo-datos.md` y `modulos.md`.
5. **Fusionar `Api` en `main`**: `main` todavía está en el commit de documentación del
   2026-11-03.
