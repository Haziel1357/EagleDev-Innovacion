# Guía de la API del backend

Cómo está organizada la API REST de `revalora-backend` y cómo añadir o modificar
endpoints sin romper el orden MVC. Para la historia de lo que se ha hecho, ve a
[bitacora-backend.md](bitacora-backend.md).

## Arrancar en 2 minutos

Desde `revalora-backend/`:

```bash
uv sync                          # instala Python 3.12 y las dependencias en .venv
cp .env.example .env             # Windows: copy .env.example .env — ajusta DATABASE_URL
uv run alembic upgrade head      # crea tablas y datos iniciales (necesita PostgreSQL)
uv run uvicorn app.main:app --reload --port 8080
```

- Swagger: http://localhost:8080/docs. Regístrate con `POST /api/v1/auth/registro` y
  después usa **Authorize** con tu correo y contraseña.
- Para las pruebas no hace falta PostgreSQL: `uv run pytest`.

> **Windows:** si la terminal dice `uv: command not found`, uv está instalado en
> `%USERPROFILE%\.local\bin`, que no está en el PATH. Abre una terminal nueva o añade esa
> carpeta al PATH.

## Cómo viaja una petición

```
Petición HTTP
   │
   ▼
controllers/api/<modulo>/x_controller.py   recibe, valida con un schema y llama al servicio
   │                                        (no contiene lógica de negocio ni consultas)
   ▼
services/<modulo>/x_service.py             reglas de negocio; lanza excepciones de app/exceptions;
   │                                        hace db.commit()
   ▼
repositories/<modulo>/x_repository.py      consultas SQLAlchemy (no hace commit)
   │
   ▼
models/<modulo>/x.py                       tablas (SQLAlchemy)
```

La respuesta vuelve convertida en un esquema `...Response` de `app/schemas/<modulo>_schema.py`.

## Dónde va cada cosa

| Qué | Dónde |
|---|---|
| Endpoint JSON | `app/controllers/api/<modulo>/<entidad>_controller.py` |
| Página HTML | `app/controllers/web/<modulo>/<entidad>_controller.py` + `app/templates/<modulo>/` |
| Registro de routers | `app/controllers/router.py` (`_CONTROLADORES_API` o `_CONTROLADORES_WEB`) |
| Entrada y salida (Pydantic) | `app/schemas/<modulo>_schema.py` (`XRequest`, `XResponse`) |
| Lógica de negocio | `app/services/<modulo>/` |
| Consultas | `app/repositories/<modulo>/` (heredan de `base_repository.py`) |
| Tablas | `app/models/<modulo>/`, importadas en `app/models/__init__.py` |
| Errores de negocio | `app/exceptions/errores.py` |
| Constantes (pesos de coincidencia, etc.) | `app/utils/constantes.py` |
| Llamadas al servicio de IA | solo a través de `app/services/ia/ia_service_client.py` |

## Reglas de la API

- **Prefijo.** Todo endpoint JSON vive bajo `/api/v1`. El prefijo lo pone `router.py`
  (`PREFIJO_API` en `app/core/config.py`); en el controlador solo se escribe el prefijo
  del módulo, por ejemplo `APIRouter(prefix="/materiales", ...)`. La prueba
  `test_rutas_de_api_tienen_prefijo` falla si una ruta queda fuera.
- **Errores.** No uses `HTTPException`; lanza la excepción de negocio correspondiente y el
  manejador global responde con el formato común
  `{"estado", "error", "mensaje", "ruta", "detalles"?}`:

  | Excepción | Código |
  |---|---|
  | `ArchivoInvalidoError` | 400 |
  | `NoAutenticadoError` | 401 |
  | `AccesoDenegadoError` | 403 |
  | `RecursoNoEncontradoError` | 404 |
  | `ReglaNegocioError` | 409 |
  | `DatosInvalidosError` | 422 |
  | `IaServiceError` | 502 |

- **Autenticación.** Se declara con las dependencias de
  `app/security/usuario_autenticado.py`:

  | Dependencia | Exige |
  |---|---|
  | `UsuarioOpcional` | nada (el usuario puede no tener sesión) |
  | `UsuarioActual` | sesión iniciada |
  | `EmpresaActual` | sesión y empresa registrada |
  | `AdminActual` | rol `ADMIN` |

- **Listados.** Se paginan con `PaginacionDep` y `construir_pagina` (`app/utils/paginacion.py`)
  y devuelven `PaginaResponse[...]`.
- **Mensajes en español**, igual que los nombres del dominio (`material`, `necesidad`, ...).
- **Al modificar y devolver una entidad** cuyas relaciones pudieron cambiar (por ejemplo,
  al cambiar `categoria_id`), haz `db.refresh(entidad)` después del `commit`. Si no, la
  respuesta muestra la relación anterior; así se produjo el bug corregido en necesidades.

## Añadir un endpoint (receta)

1. **Esquema:** `XRequest` y `XResponse` en `app/schemas/<modulo>_schema.py`.
2. **Repositorio**, si hace falta una consulta nueva.
3. **Servicio:** el método con las reglas de negocio. Lanza excepciones de
   `app/exceptions` y termina con `db.commit()`.
4. **Controlador** en `app/controllers/api/<modulo>/`, con `response_model` y `status_code`.
5. Si es un controlador nuevo, **regístralo** en `_CONTROLADORES_API` de `router.py`.
6. Si añadiste o cambiaste un modelo, crea la **migración**:
   `uv run alembic revision --autogenerate -m "..."`. Revísala antes de subirla.
7. **Prueba** en `tests/controllers/api/<modulo>/` con el `client` y los ayudantes de
   `tests/conftest.py` (`registrar`, `crear_empresa`, `publicar_material`,
   `publicar_necesidad`, `ia`). Usa rutas completas (`"/api/v1/..."`).
8. Actualiza la tabla de rutas de `revalora-backend/README.md`.

## Pruebas

Organizadas con la misma estructura que `app/`:

| Carpeta | Qué prueba | Cómo |
|---|---|---|
| `tests/controllers/api/<modulo>/` | endpoints | HTTP con `TestClient` |
| `tests/services/<modulo>/` | lógica pura | llamando a la clase o función directamente |
| `tests/repositories/<modulo>/` | consultas | con la sesión `db` |

`conftest.py` monta SQLite en memoria con los datos iniciales y sustituye el cliente de IA
por `IaFalsa`. Para simular que la IA falla, usa `ia.error = IaServiceError("...")`; para
cambiar lo que responde, modifica `ia.reconocimiento`, `ia.recomendacion` o
`ia.oportunidades`.

## Antes de subir cambios

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run alembic check      # solo si tocaste modelos (necesita PostgreSQL)
```

## Relación con el servicio de IA

`revalora-ia-service` es una aplicación aparte (FastAPI, puerto 8000) para la visión
artificial y las recomendaciones. El backend la llama por HTTP en
`IA_SERVICE_URL + /api/v1/...` y solo a través de `IaServiceClient`. Si cambias lo que el
backend espera recibir, actualiza a la vez `app/schemas/ia_schema.py` y
[contrato-api-ia.md](contrato-api-ia.md).
