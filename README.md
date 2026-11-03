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
| 🤖 **Reconocimiento con IA** | Clasifica el material de la foto (madera, cartón, plástico, tela, metal) y devuelve un nivel de confianza. El usuario puede confirmar o corregir el resultado. |
| 🔎 **Buscador inteligente** | El usuario escribe lo que quiere fabricar; la IA deduce los materiales necesarios y el sistema prioriza los sobrantes que mejor se ajustan. |
| 🔗 **Motor de coincidencias** | Cruza ofertas y necesidades y calcula una puntuación de compatibilidad según material, dimensiones, cantidad, estado, ubicación y precio. |
| 🤝 **Intercambios y transacciones** | Solicitudes de compra o intercambio, aceptación o rechazo, estados e historial de operaciones. |
| 💡 **Oportunidades productivas** | Sugiere productos que se pueden fabricar con los materiales disponibles e indica qué materiales faltan. |

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

El sistema se compone de dos aplicaciones independientes que se comunican mediante **API REST**:

```
┌──────────────────────────────┐        REST / JSON        ┌──────────────────────────────┐
│      revalora-backend        │  ───────────────────────▶ │     revalora-ia-service      │
│  Java · Spring Boot (MVC)    │                           │       Python · FastAPI       │
│                              │  ◀─────────────────────── │                              │
│  Vistas · Controladores ·    │   predicciones /          │  Visión artificial ·         │
│  Servicios · Repositorios    │   recomendaciones         │  Motor de recomendaciones    │
└──────────────┬───────────────┘                           └──────────────────────────────┘
               │ JPA
               ▼
        ┌──────────────┐
        │  PostgreSQL  │
        └──────────────┘
```

**Backend (MVC)**

- **Model:** entidades JPA organizadas por módulo funcional.
- **View:** plantillas HTML, CSS y JavaScript organizadas por módulo.
- **Controller:** recibe las peticiones y delega en la capa de servicios.
- Capas de apoyo: `service` (lógica de negocio, con interfaz e implementación), `repository` (acceso a datos), `dto` (objetos de entrada y salida), `config`, `security`, `exception` y `util`.

**Servicio de IA**

- `ml/vision`: reconocimiento y clasificación de materiales a partir de imágenes.
- `ml/recomendacion`: análisis del producto a fabricar y recomendación de materiales.
- El backend Java se comunica con este servicio únicamente a través de `IaServiceClient`, de modo que el modelo puede cambiar sin afectar a la aplicación principal.

---

## 🛠️ Tecnologías

**Aplicación principal**

- Java
- Spring Boot
- Maven
- Spring Data JPA
- PostgreSQL
- HTML, CSS y JavaScript

**Servicio de inteligencia artificial**

- Python
- FastAPI
- Modelo de visión artificial *(por definir)*
- Módulo de recomendaciones inteligentes *(por definir)*

---

## 📁 Estructura del proyecto

```
REVALORA/
├── revalora-backend/
│   ├── pom.xml
│   └── src/
│       ├── main/
│       │   ├── java/com/revalora/
│       │   │   ├── config/
│       │   │   ├── controller/      (usuario, empresa, material, necesidad, ia,
│       │   │   ├── model/            buscador, coincidencia, transaccion,
│       │   │   ├── repository/       oportunidad)
│       │   │   ├── service/
│       │   │   ├── dto/
│       │   │   ├── exception/
│       │   │   ├── security/
│       │   │   └── util/
│       │   └── resources/
│       │       ├── templates/       (vistas HTML por módulo)
│       │       ├── static/          (css, js, img)
│       │       └── application.properties
│       └── test/
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

El árbol completo está en [`ESTRUCTURA.txt`](ESTRUCTURA.txt).

---

## ⚙️ Requisitos previos

- JDK 17 o superior
- Maven 3.8 o superior
- PostgreSQL 14 o superior
- Python 3.10 o superior
- Git

---

## 🚀 Instalación y ejecución

> ⚠️ El proyecto se encuentra en fase de estructura. Estos pasos quedarán operativos a medida que se implementen los módulos.

**1. Clonar el repositorio**

```bash
git clone <url-del-repositorio>
cd REVALORA
```

**2. Base de datos**

```sql
CREATE DATABASE revalora;
```

Configura las credenciales en `revalora-backend/src/main/resources/application-dev.properties`.

**3. Backend (Spring Boot)**

```bash
cd revalora-backend
mvn spring-boot:run
```

**4. Servicio de IA (FastAPI)**

```bash
cd revalora-ia-service
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

---

## 📊 Estado del proyecto

🟡 **En desarrollo:** fase de definición de la estructura.

- [x] Definición de la idea y alineación con los ODS
- [x] Estructura de carpetas y archivos (MVC + servicio de IA)
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
