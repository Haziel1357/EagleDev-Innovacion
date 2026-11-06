# ♻️ REVALORA

**Plataforma inteligente para el intercambio y aprovechamiento de materiales sobrantes entre microempresas, pequeñas empresas y emprendimientos.**

> Lo que para una empresa es un desperdicio, para otra puede convertirse en materia prima.

---

## 📌 Tabla de contenidos

- [Descripción](#-descripción)
- [Problemática](#-problemática)
- [Alineación con los ODS](#-alineación-con-los-ods)
- [Funcionalidades](#-funcionalidades)
- [Ejemplo de uso](#-ejemplo-de-uso)
- [Arquitectura](#-arquitectura)
- [Tecnologías](#-tecnologías)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Requisitos previos](#-requisitos-previos)
- [Instalación y ejecución](#-instalación-y-ejecución)
- [Estado del proyecto](#-estado-del-proyecto)
- [Hoja de ruta](#-hoja-de-ruta)
- [Equipo](#-equipo)

---

## 📖 Descripción

REVALORA conecta a las empresas que generan materiales sobrantes en sus procesos productivos con otras empresas y emprendimientos que necesitan esos mismos materiales como materia prima.

Los usuarios pueden publicar sus sobrantes tomando una fotografía. Un módulo de **inteligencia artificial** reconoce el tipo de material para verificar que la publicación sea real y para mostrar su estado a los interesados. Además, la plataforma incluye un **buscador inteligente** en el que el usuario describe lo que quiere fabricar y el sistema le sugiere los materiales disponibles que le sirven.

---

## ❗ Problemática

- Muchas microempresas generan sobrantes (madera, cartón, plástico, tela, metal) que terminan desechados por no saber cómo aprovecharlos.
- Al mismo tiempo, otros emprendimientos compran esos mismos materiales nuevos, a mayor costo.
- No existe un canal confiable que conecte ambas necesidades ni que garantice que lo publicado sea real.

---

## 🌍 Alineación con los ODS

| Meta | Descripción | Aporte de REVALORA |
|------|-------------|--------------------|
| **ODS 8.3** | Promover el emprendimiento, la innovación y el crecimiento de las micro y pequeñas empresas. | Reduce costos de materia prima y abre nuevas fuentes de ingreso con la venta de sobrantes. |
| **ODS 8.4** | Mejorar la eficiencia en el uso de los recursos y reducir el desperdicio. | Da una segunda vida a los materiales y evita que terminen como residuo. |

---

## ✨ Funcionalidades

| Módulo | Descripción |
|--------|-------------|
| 👤 **Usuarios y empresas** | Registro, inicio de sesión, perfiles, datos de la empresa, ubicación y actividad económica. |
| 📦 **Materiales sobrantes** | Publicación de materiales con fotos, cantidad, unidad de medida, dimensiones, estado, ubicación y precio. Pueden ofrecerse para venta, intercambio o aprovechamiento. |
| 📋 **Necesidades de materiales** | Las empresas publican lo que necesitan: tipo de material, cantidad, estado mínimo aceptable y presupuesto. |
| 🤖 **Reconocimiento con IA** | Clasifica el material de la foto (madera, cartón, plástico, tela, metal, vidrio, papel u otro) y devuelve un nivel de confianza. El usuario puede confirmar o corregir el resultado. |
| 🔎 **Buscador inteligente** | El usuario escribe lo que quiere fabricar; la IA deduce los materiales necesarios y el sistema prioriza los sobrantes que mejor se ajustan. |
| 🔗 **Motor de coincidencias** | Cruza ofertas y necesidades y calcula una puntuación de compatibilidad según material, dimensiones, cantidad, estado, ubicación y precio. |
| 🤝 **Intercambios y transacciones** | Solicitudes de compra o intercambio, aceptación o rechazo, estados e historial de operaciones. |
| 💡 **Oportunidades productivas** | Sugiere productos que se pueden fabricar con los materiales disponibles e indica qué materiales faltan. |
| 📱 **App instalable (PWA)** | Se instala en el celular o el computador como una aplicación, con su propio ícono y ventana, y muestra una página de aviso cuando no hay conexión. |

---

## 🧪 Ejemplo de uso

**Publicar un sobrante**

1. Una fábrica de muebles tiene retazos de madera que ya no usa.
2. El dueño toma una foto y la sube a REVALORA.
3. La IA reconoce el material como *madera* y el dueño completa la cantidad, las dimensiones y el estado.
4. Un taller de artesanías encuentra la publicación y envía una solicitud de compra o intercambio.

**Buscar por producto**

1. Un emprendedor escribe: *"Quiero fabricar marcos para cuadros"*.
2. La IA identifica los materiales necesarios: madera (estructura), vidrio (protección) y cartón (respaldo).
3. REVALORA busca esos materiales entre las publicaciones y muestra primero los que mejor se ajustan por compatibilidad, cercanía, cantidad y precio.

---

## 🏗️ Arquitectura

El sistema se compone de dos aplicaciones Python independientes que se comunican mediante **API REST**:

```
┌──────────────────────────────┐        REST / JSON        ┌──────────────────────────────┐
│      revalora-backend        │  ───────────────────────▶ │     revalora-ia-service      │
│  Python · FastAPI (MVC)      │                           │       Python · FastAPI       │
│  :8080                       │  ◀─────────────────────── │       :8000                  │
│  Vistas · Controladores ·    │   predicciones /          │  Visión artificial ·         │
│  Servicios · Repositorios    │   recomendaciones         │  Motor de recomendaciones    │
└──────────────┬───────────────┘                           └──────────────────────────────┘
               │ SQLAlchemy
               ▼
        ┌──────────────┐
        │  PostgreSQL  │
        └──────────────┘
```

**Backend (MVC)**

- **Model:** modelos SQLAlchemy organizados por módulo funcional (`app/models`).
- **View:** plantillas Jinja2, CSS y JavaScript organizadas por módulo (`app/templates`, `app/static`).
- **Controller:** routers de FastAPI que reciben las peticiones y delegan en la capa de servicios (`app/controllers`). Se dividen en `controllers/api/` (API REST en JSON, bajo `/api/v1`) y `controllers/web/` (páginas HTML que renderizan las vistas).
- Capas de apoyo: `services` (lógica de negocio), `repositories` (acceso a datos), `schemas` (esquemas Pydantic de entrada y salida), `core` (configuración y base de datos), `security`, `exceptions` y `utils`.

**Servicio de IA**

- `ml/vision`: reconocimiento del material de una foto con el modelo CLIP (*zero-shot*, sin entrenamiento propio), con un clasificador por color y textura como respaldo.
- `ml/recomendacion`: catálogo de productos (`catalogo_productos.json`) y análisis del texto en español para recomendar materiales y sugerir oportunidades productivas.
- El backend se comunica con este servicio únicamente a través de `app/services/ia/ia_service_client.py`, de modo que el modelo puede cambiar sin afectar a la aplicación principal.

---

## 🛠️ Tecnologías

**Aplicación principal**

- Python
- FastAPI + Uvicorn
- SQLAlchemy 2 + Alembic (migraciones)
- Pydantic
- Jinja2
- PostgreSQL
- HTML, CSS y JavaScript
- Aplicación web progresiva (PWA): manifest y service worker

**Servicio de inteligencia artificial**

- Python
- FastAPI
- PyTorch (solo CPU) + Hugging Face Transformers: modelo de visión CLIP (`openai/clip-vit-base-patch32`)
- Pillow y NumPy (procesamiento de imágenes)
- Motor de recomendaciones basado en un catálogo de productos

**Herramientas**

- [uv](https://docs.astral.sh/uv/) (versión de Python, entorno virtual y dependencias de las dos aplicaciones)
- pytest (pruebas)
- Ruff (formato y análisis de código)

---

## 📁 Estructura del proyecto

```
REVALORA/
├── revalora-backend/
│   ├── pyproject.toml           (dependencias, gestionadas con uv)
│   ├── uv.lock
│   ├── .python-version
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/                 (migraciones)
│   ├── app/
│   │   ├── main.py
│   │   ├── core/                (config, base de datos, logging, web)
│   │   ├── controllers/
│   │   │   ├── api/             (JSON bajo /api/v1: usuario, empresa, material,
│   │   │   │                     necesidad, ia, buscador, coincidencia,
│   │   │   │                     transaccion, oportunidad)
│   │   │   └── web/             (páginas HTML con Jinja2)
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── exceptions/
│   │   ├── security/
│   │   ├── utils/
│   │   ├── templates/           (vistas Jinja2 por módulo)
│   │   └── static/              (css, js, img)
│   ├── uploads/
│   └── tests/
├── revalora-ia-service/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── ml/
│   │   │   ├── vision/
│   │   │   └── recomendacion/
│   │   └── utils/
│   ├── modelos_entrenados/
│   ├── datos/
│   ├── notebooks/
│   └── tests/
└── docs/
```

El árbol completo está en [`ESTRUCTURA.txt`](ESTRUCTURA.txt). El archivo `uv.lock` fija las versiones exactas de las dependencias y se sube al repositorio para que todo el equipo instale lo mismo.

---

## ⚙️ Requisitos previos

- [uv](https://docs.astral.sh/uv/) (instala por sí solo Python 3.12, la versión indicada en `revalora-backend/.python-version`)
- PostgreSQL 14 o superior
- Git

---

## 🚀 Instalación y ejecución

> El backend y el servicio de IA son funcionales. Si el servicio de IA no está levantado, las rutas de reconocimiento, buscador inteligente y oportunidades del backend responden 502; el resto funciona igual.

**0. Instalar uv** (solo una vez)

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux y macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**1. Clonar el repositorio**

```bash
git clone https://github.com/Haziel1357/EagleDev-Innovacion.git
cd EagleDev-Innovacion
```

**2. Base de datos**

```sql
CREATE DATABASE revalora;
```

Configura las credenciales en `DATABASE_URL`, dentro de `revalora-backend/.env` (se crea en el paso 3).

**3. Backend (FastAPI)**

```bash
cd revalora-backend
uv sync                         # crea .venv e instala las dependencias
cp .env.example .env            # En Windows: copy .env.example .env
uv run alembic upgrade head     # crea las tablas y los datos iniciales
uv run uvicorn app.main:app --reload --port 8080
```

La aplicación queda en http://localhost:8080, la API REST en http://localhost:8080/api/v1 y su documentación en http://localhost:8080/docs. Las pruebas se ejecutan con `uv run pytest`. Más detalles en [`revalora-backend/README.md`](revalora-backend/README.md).

**4. Servicio de IA (FastAPI)**

```bash
cd revalora-ia-service
uv sync                                          # dependencias (~800 MB, PyTorch solo-CPU)
uv run python -m app.ml.vision.descargar_modelo  # modelo CLIP (~600 MB, una sola vez)
uv run uvicorn app.main:app --reload --port 8000
```

Documentación en http://localhost:8000/docs y salud en http://localhost:8000/api/v1/salud. El backend lo busca en `IA_SERVICE_URL` (por defecto `http://localhost:8000`). Pasa siempre `--port` a los dos servicios: `uvicorn` sin `--port` usa el 8000 y el backend ocuparía el puerto de la IA. Más detalles y cómo probarlo en [`revalora-ia-service/README.md`](revalora-ia-service/README.md).

---

## 📊 Estado del proyecto

🟡 **En desarrollo:** fase de definición de la estructura.

- [x] Definición de la idea y alineación con los ODS
- [x] Estructura de carpetas y archivos (MVC + servicio de IA)
- [x] Migración del backend de Java (Spring Boot) a Python (FastAPI)
- [x] Gestión de dependencias del backend con uv (`pyproject.toml` + `uv.lock`)
- [x] API REST del backend para todos los módulos, con migraciones y pruebas
- [x] Servicio de IA: reconocimiento de materiales (CLIP), recomendación de materiales y oportunidades productivas, con pruebas
- [x] Aplicación web progresiva (PWA): instalable y con página sin conexión
- [ ] Modelo de datos y diagrama entidad-relación
- [ ] Gestión de usuarios y empresas
- [ ] Publicación de materiales y necesidades
- [ ] Integración del reconocimiento de materiales con IA
- [ ] Buscador inteligente para fabricación
- [ ] Motor de coincidencias
- [ ] Intercambios y transacciones
- [ ] Generador de oportunidades productivas

---

## 🗺️ Hoja de ruta

1. **Fase 1:** modelo de datos, autenticación y registro de empresas.
2. **Fase 2:** publicación de materiales y necesidades, con búsqueda tradicional.
3. **Fase 3:** servicio de IA para el reconocimiento de materiales.
4. **Fase 4:** buscador inteligente y motor de coincidencias.
5. **Fase 5:** transacciones, historial y oportunidades productivas.

---

## 👥 Equipo

| Nombre | Rol |
|--------|-----|
| *Por completar* | *Por completar* |

---

<p align="center">Hecho con 💚 para impulsar la economía circular entre emprendimientos.</p>
