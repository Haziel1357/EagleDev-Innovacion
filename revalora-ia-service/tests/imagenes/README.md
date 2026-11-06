# Fotos para evaluar el reconocimiento

Pon aquí fotos reales de materiales para comprobar qué tan bien los reconoce el modelo.

- Nombre: `<material>_<numero>.<ext>`, por ejemplo `madera_1.jpg` o `vidrio_3.png`.
- `<material>` debe ser un código válido: `madera`, `carton`, `plastico`, `tela`, `metal`,
  `vidrio`, `papel` u `otro`.
- Formatos: JPG, PNG o WEBP.
- Usa fotos propias o con licencia que permita subirlas al repositorio.

Ejecuta:

```bash
uv run pytest -m modelo -v
```

Cada foto es una prueba: si falla, el mensaje muestra las tres predicciones con más
confianza. Si un material falla a menudo, añade descripciones en inglés a
`descripciones_clip` en `app/ml/materiales.py` (por ejemplo `"a photo of rusty iron scrap"`).
