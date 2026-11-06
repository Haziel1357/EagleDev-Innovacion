# revalora-backend

Aplicación principal de REVALORA: **Python · FastAPI** con arquitectura MVC (vistas Jinja2, controladores, servicios y repositorios) sobre **PostgreSQL**. Las dependencias y el entorno virtual se gestionan con **[uv](https://docs.astral.sh/uv/)**.

## Requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (instala por sí solo Python 3.12, la versión de `.python-version`)
- PostgreSQL 14 o superior

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux y macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Ejecución en desarrollo

```bash
uv sync                          # crea .venv e instala dependencias (incluye las de desarrollo)
cp .env.example .env             # En Windows: copy .env.example .env  — ajusta DATABASE_URL
uv run alembic upgrade head      # crea las tablas y los datos iniciales
uv run uvicorn app.main:app --reload --port 8080
```

- Aplicación (páginas HTML): http://localhost:8080
- API REST (JSON): http://localhost:8080/api/v1
- Documentación de la API (Swagger): http://localhost:8080/docs — usa el botón **Authorize** con tu correo y contraseña.
- Salud: http://localhost:8080/api/v1/salud

El servicio de IA (`revalora-ia-service`) corre por separado en el puerto 8000 (`IA_SERVICE_URL`). Si no está levantado, las rutas que lo usan (`/ia/reconocimiento`, `/buscador/inteligente`, `/oportunidades/analizar`) responden **502**; el resto de la aplicación funciona igual.

## Comandos de uv

```bash
uv add <paquete>                 # añadir una dependencia
uv add --dev <paquete>           # añadir una dependencia de desarrollo
uv remove <paquete>              # quitar una dependencia
uv lock --upgrade                # actualizar versiones dentro de los rangos de pyproject.toml
uv run pytest                    # pruebas
uv run ruff check .              # análisis de código
uv run ruff format .             # formato
```

`uv.lock` fija las versiones exactas y **se sube al repositorio**, para que todo el equipo instale lo mismo.

## Pruebas

```bash
uv run pytest
```

Las pruebas usan SQLite en memoria y un cliente de IA simulado: no necesitan PostgreSQL ni el servicio de IA.

## Migraciones (Alembic)

```bash
uv run alembic revision --autogenerate -m "descripcion del cambio"
uv run alembic upgrade head
uv run alembic check             # comprueba que los modelos y las migraciones coinciden
```

- `0001_esquema_inicial`: todas las tablas.
- `0002_datos_iniciales`: roles (`ADMIN`, `EMPRESA`), categorías de material (madera, cartón, plástico, tela, metal, vidrio, papel, otro) y actividades económicas.

Para que `--autogenerate` detecte un modelo nuevo, impórtalo en `app/models/__init__.py`. Los enums se guardan como `VARCHAR`, así que añadir un valor no requiere migración.

Para dar rol de administrador a una cuenta (no hay endpoint para eso, a propósito):

```sql
UPDATE usuarios SET rol_id = (SELECT id FROM roles WHERE nombre = 'ADMIN') WHERE email = 'tu@correo.com';
```

## API

Todas las rutas de la API llevan el prefijo **`/api/v1`** (definido en `PREFIJO_API`, `app/core/config.py`); en la tabla se omite por brevedad. Así `/materiales` queda libre para la página HTML y `/api/v1/materiales` es el JSON. Bajo `/api/v1` los errores responden siempre en JSON, aunque la petición venga del navegador.

Autenticación con JWT: `Authorization: Bearer <token>` (o la cookie `access_token` que dejan `/auth/registro` y `/auth/login`). Casi todo lo que publica o solicita requiere que la cuenta tenga una empresa registrada (`POST /empresas`).

| Módulo | Rutas principales |
|---|---|
| Autenticación | `POST /auth/registro`, `POST /auth/login`, `POST /auth/token` (Swagger), `POST /auth/logout` |
| Usuarios | `GET/PUT /usuarios/me`; administración: `GET /usuarios`, `PATCH /usuarios/{id}/activo` |
| Empresas | `POST /empresas`, `GET /empresas/mia`, `GET /empresas`, `GET/PUT /empresas/{id}`, `GET /empresas/actividades` |
| Categorías | `GET /categorias`; administración: `POST`, `PUT /categorias/{id}` |
| Materiales | `POST /materiales`, `GET /materiales`, `GET /materiales/mios`, `GET/PUT/DELETE /materiales/{id}`, `PATCH /materiales/{id}/disponibilidad`, fotos en `/materiales/{id}/fotos` |
| Necesidades | `POST /necesidades`, `GET /necesidades`, `GET /necesidades/mias`, `GET/PUT/DELETE /necesidades/{id}`, `PATCH /necesidades/{id}/estado` |
| Reconocimiento IA | `POST /ia/reconocimiento` (foto), `POST /ia/clasificaciones/{id}/confirmar`, `GET /ia/clasificaciones` |
| Buscador | `POST /buscador/inteligente`, `GET /buscador/inteligente/historial`, `GET /buscador/tradicional` |
| Coincidencias | `GET /coincidencias`, `GET /coincidencias/materiales/{id}`, `GET /coincidencias/necesidades/{id}`, `POST …/recalcular` |
| Solicitudes | `POST /solicitudes`, `GET /solicitudes/enviadas`, `GET /solicitudes/recibidas`, `POST /solicitudes/{id}/aceptar · rechazar · cancelar · completar` |
| Historial | `GET /historial`, `GET /historial/solicitudes/{id}` |
| Oportunidades | `POST /oportunidades/analizar`, `GET /oportunidades`, `GET /oportunidades/{id}` |

Los errores responden siempre con el mismo formato: `{"estado", "error", "mensaje", "ruta", "detalles"?}`.

### Flujos principales

**Publicar con foto.** `POST /ia/reconocimiento` con la imagen → la IA sugiere la categoría y su confianza → `POST /materiales` con los datos y el `clasificacion_id`. La foto queda como principal del material; si la categoría elegida coincide con la sugerida, el material queda `verificado_ia: true` (si no, la clasificación queda `CORREGIDA`).

**Coincidencias.** Al publicar o modificar un material o una necesidad se cruzan automáticamente con los de la misma categoría de otras empresas. La puntuación (0-100) pondera material 25 %, cantidad 20 %, estado 15 %, dimensiones 10 %, ubicación 15 % y precio 15 %; solo se guardan las de 40 o más (`app/utils/constantes.py`). El precio del material es por unidad de medida; el presupuesto de la necesidad es el total.

**Solicitudes.** El tipo debe corresponder a la oferta del material (VENTA → `COMPRA`, INTERCAMBIO → `INTERCAMBIO` con `material_ofrecido_id`, APROVECHAMIENTO → `APROVECHAMIENTO`). Al aceptar se descuenta la cantidad; si el material se agota, las demás solicitudes pendientes se rechazan solas. Cada cambio de estado queda en el historial.

## Estructura

```
revalora-backend/
├── pyproject.toml         Dependencias y configuración de pytest y Ruff
├── uv.lock                Versiones exactas (generado por uv; se versiona)
├── .python-version        Versión de Python que usa uv (3.12)
├── app/
│   ├── main.py            Punto de entrada (crea la app FastAPI)
│   ├── core/              Configuración, base de datos, logging, plantillas y estáticos
│   ├── controllers/       Routers de FastAPI (router.py los reúne)
│   │   ├── api/           API REST en JSON bajo /api/v1, una carpeta por módulo
│   │   └── web/           Páginas HTML que renderizan las plantillas
│   ├── models/            Modelos SQLAlchemy por módulo (enums.py por módulo)
│   ├── repositories/      Acceso a datos (base_repository.py con lo común)
│   ├── services/          Lógica de negocio (incluye el cliente del servicio de IA)
│   ├── schemas/           Esquemas Pydantic de entrada y salida
│   ├── security/          Contraseñas, tokens y usuario autenticado
│   ├── exceptions/        Excepciones de negocio y manejadores globales
│   ├── utils/             Constantes, paginación, distancias y validación de archivos
│   ├── templates/         Vistas Jinja2 por módulo
│   └── static/            css, js, img
├── alembic/               Migraciones de base de datos
├── tests/                 Pruebas (pytest), con la misma organización que app/:
│   ├── controllers/api/   Pruebas de la API por HTTP (TestClient)
│   ├── services/          Pruebas unitarias de lógica de negocio
│   └── repositories/      Pruebas de consultas a la base de datos
└── uploads/               Fotos subidas (no se versiona)
```

Módulos: `usuario`, `empresa`, `material`, `necesidad`, `ia`, `buscador`, `coincidencia`, `transaccion`, `oportunidad`.

## Equivalencias con la estructura anterior (Spring Boot)

| Spring Boot | Python |
|---|---|
| `pom.xml` + Maven | `pyproject.toml` + `uv.lock` (uv) |
| `RevaloraApplication.java` | `app/main.py` |
| `application*.properties` | `.env` + `app/core/config.py` (variable `ENTORNO`) |
| `config/JpaConfig` | `app/core/database.py` |
| `config/WebMvcConfig`, `config/FileStorageConfig` | `app/core/web.py` |
| `config/IaServiceClientConfig` | `IA_SERVICE_URL` / `IA_SERVICE_TIMEOUT` en `app/core/config.py` |
| `controller/<modulo>/XController` (`@RestController`) | `app/controllers/api/<modulo>/x_controller.py` |
| `controller/<modulo>/XController` (`@Controller`, vistas) | `app/controllers/web/<modulo>/x_controller.py` |
| `model/<modulo>/` (entidades JPA) | `app/models/<modulo>/` (SQLAlchemy) |
| `repository/` (Spring Data) | `app/repositories/` |
| `service/` + `service/impl/` | `app/services/` (sin separar interfaz e implementación) |
| `dto/<modulo>/request` y `response` | `app/schemas/<modulo>_schema.py` (Pydantic) |
| `security/` (Spring Security) | `app/security/` |
| `exception/` + `GlobalExceptionHandler` | `app/exceptions/errores.py` + `handlers.py` |
| `resources/templates` (Thymeleaf) | `app/templates` (Jinja2) |
| `resources/static` | `app/static` |
| Esquema de BD con JPA / Hibernate | Migraciones con Alembic |
| `mvn spring-boot:run` | `uv run uvicorn app.main:app --reload --port 8080` |
