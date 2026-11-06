# Contrato entre revalora-backend y revalora-ia-service

El backend se comunica con el servicio de IA **solo** a través de `IaServiceClient`
(`revalora-backend/app/services/ia/ia_service_client.py`). Las respuestas se validan con
los esquemas de la sección *Contrato* de `revalora-backend/app/schemas/ia_schema.py`.

- URL base: `IA_SERVICE_URL` (por defecto `http://localhost:8000`) + prefijo `/api/v1`.
- Tiempo de espera: `IA_SERVICE_TIMEOUT` segundos (por defecto 10).
- Los códigos de material son los `codigo` de `categorias_material`, en minúsculas y sin
  tildes: `madera`, `carton`, `plastico`, `tela`, `metal`, `vidrio`, `papel`, `otro`.
  Si la IA devuelve un código que no existe, el backend lo guarda igualmente pero sin
  categoría asociada.
- Si el servicio no responde, responde con un código 4xx/5xx o devuelve un JSON que no
  cumple el contrato, el backend responde **502** al cliente con un mensaje en español.

## `POST /api/v1/reconocimiento`

Clasifica el material de una foto.

**Petición:** `multipart/form-data` con el campo `imagen` (JPG, PNG o WEBP; el backend
ya validó tipo y tamaño).

**Respuesta 200:**

```json
{
  "material": "madera",
  "confianza": 0.93,
  "predicciones": [
    { "material": "madera", "confianza": 0.93 },
    { "material": "carton", "confianza": 0.05 }
  ]
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `material` | string | sí | Material con mayor confianza. |
| `confianza` | número 0-1 | sí | Por debajo de 0.6 el backend marca `confianza_baja`. |
| `predicciones` | lista | no | Alternativas ordenables por confianza. |
| `modelo` | string | no | Clasificador que respondió (`clip` o `heuristico`). El backend lo ignora; sirve para depurar. |

**Errores:** `400` si el archivo está vacío, dañado o no es JPG/PNG/WEBP; `413` si supera
`TAMANO_MAXIMO_IMAGEN_MB`; `422` si falta el campo `imagen`; `503` si el modelo no está
disponible (solo con `MODELO_VISION=clip`). El backend convierte cualquiera de ellos en 502.

## `POST /api/v1/recomendacion`

Deduce los materiales necesarios para fabricar un producto descrito en lenguaje natural.

**Petición:**

```json
{ "descripcion": "Quiero fabricar marcos para cuadros" }
```

**Respuesta 200:**

```json
{
  "producto": "marco para cuadros",
  "materiales": [
    { "material": "madera", "funcion": "estructura", "cantidad_estimada": 2, "unidad": "METRO" },
    { "material": "vidrio", "funcion": "protección" },
    { "material": "carton", "funcion": "respaldo" }
  ]
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `producto` | string | no | Nombre del producto interpretado. |
| `materiales[].material` | string | sí | Código del material. |
| `materiales[].funcion` | string | no | Para qué sirve en el producto. |
| `materiales[].cantidad_estimada` | número | no | Se usa para priorizar publicaciones con cantidad suficiente. |
| `materiales[].unidad` | string | no | `UNIDAD`, `KILOGRAMO`, `METRO`, `METRO_CUADRADO`, `METRO_CUBICO` o `LITRO`. |

## `POST /api/v1/oportunidades`

Sugiere productos que se pueden fabricar con los materiales disponibles.

**Petición:**

```json
{ "materiales": ["madera", "tela"], "max_productos": 5 }
```

**Respuesta 200:**

```json
{
  "productos": [
    {
      "nombre": "Marcos para cuadros",
      "descripcion": "Marcos rústicos con retazos de madera.",
      "viabilidad": 0.9,
      "materiales_utilizados": ["madera"],
      "materiales_faltantes": [{ "material": "vidrio", "descripcion": "Para el frente" }]
    }
  ]
}
```

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `productos[].nombre` | string | sí | |
| `productos[].descripcion` | string | no | |
| `productos[].viabilidad` | número 0-1 | no | Por defecto 0. El backend ordena por este valor. |
| `productos[].materiales_utilizados` | lista de strings | no | |
| `productos[].materiales_faltantes` | lista | no | El backend añade cuántas publicaciones disponibles hay de cada uno. |

## `GET /api/v1/salud`

Verificación de que el servicio está activo. El backend no la usa todavía.

```json
{ "estado": "ok", "modelo_vision": "clip" }
```

`modelo_vision`: `clip`, `heuristico` (respaldo poco preciso) o `sin_cargar` (con
`CARGAR_MODELO_AL_INICIAR=false`, hasta la primera foto).

## Formato de los errores

Igual que el backend: `{"estado", "error", "mensaje", "ruta", "detalles"?}`. Las peticiones
con datos inválidos responden `422` con `detalles` (campo y mensaje).

## Implementación

La implementación de referencia es `revalora-ia-service` (ver su README). Si cambias este
contrato, actualiza a la vez `revalora-ia-service/app/schemas/` y
`revalora-backend/app/schemas/ia_schema.py`.
