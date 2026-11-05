# revalora-backend

Aplicación principal de REVALORA: **Python · FastAPI** con arquitectura MVC (vistas Jinja2, controladores, servicios y repositorios) sobre **PostgreSQL**.

## Ejecución en desarrollo

```bash
python -m venv venv
venv\Scripts\activate            # Linux/macOS: source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env             # ajusta DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

- Aplicación: http://localhost:8080
- Documentación de la API (Swagger): http://localhost:8080/docs
- Salud: http://localhost:8080/salud

El servicio de IA (`revalora-ia-service`) corre por separado en el puerto 8000 (`IA_SERVICE_URL`).

## Pruebas

```bash
pytest
```

## Migraciones (Alembic)

```bash
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```

Para que `--autogenerate` detecte un modelo nuevo, impórtalo en `app/models/__init__.py`.

## Estructura

```
revalora-backend/
├── app/
│   ├── main.py            Punto de entrada (crea la app FastAPI)
│   ├── core/              Configuración, base de datos, logging, plantillas y estáticos
│   ├── controllers/       Routers de FastAPI por módulo (router.py los reúne)
│   ├── models/            Modelos SQLAlchemy por módulo (enums.py por módulo)
│   ├── repositories/      Acceso a datos
│   ├── services/          Lógica de negocio (incluye el cliente del servicio de IA)
│   ├── schemas/           Esquemas Pydantic de entrada y salida
│   ├── security/          Contraseñas, tokens y usuario autenticado
│   ├── exceptions/        Excepciones de negocio y manejadores globales
│   ├── utils/             Utilidades
│   ├── templates/         Vistas Jinja2 por módulo
│   └── static/            css, js, img
├── alembic/               Migraciones de base de datos
├── tests/                 Pruebas (pytest)
└── uploads/               Fotos subidas (no se versiona)
```

Módulos: `usuario`, `empresa`, `material`, `necesidad`, `ia`, `buscador`, `coincidencia`, `transaccion`, `oportunidad`.

## Equivalencias con la estructura anterior (Spring Boot)

| Spring Boot | Python |
|---|---|
| `RevaloraApplication.java` | `app/main.py` |
| `application*.properties` | `.env` + `app/core/config.py` (variable `ENTORNO`) |
| `config/JpaConfig` | `app/core/database.py` |
| `config/WebMvcConfig`, `config/FileStorageConfig` | `app/core/web.py` |
| `config/IaServiceClientConfig` | `IA_SERVICE_URL` / `IA_SERVICE_TIMEOUT` en `app/core/config.py` |
| `controller/<modulo>/XController` | `app/controllers/<modulo>/x_controller.py` |
| `model/<modulo>/` (entidades JPA) | `app/models/<modulo>/` (SQLAlchemy) |
| `repository/` (Spring Data) | `app/repositories/` |
| `service/` + `service/impl/` | `app/services/` (sin separar interfaz e implementación) |
| `dto/<modulo>/request` y `response` | `app/schemas/<modulo>_schema.py` (Pydantic) |
| `security/` (Spring Security) | `app/security/` |
| `exception/` + `GlobalExceptionHandler` | `app/exceptions/errores.py` + `handlers.py` |
| `resources/templates` (Thymeleaf) | `app/templates` (Jinja2) |
| `resources/static` | `app/static` |
| Esquema de BD con JPA / Hibernate | Migraciones con Alembic |
| `mvn spring-boot:run` | `uvicorn app.main:app --reload --port 8080` |
