# Resultados: Code Analyzer

6 ejecuciones de `code_analyzer.py`: 3 archivos míos con temperatura 0.2 y 0.8. He comprobado cada bug leyendo el código. En lugar de un archivo del PSO (no está en este repo) usé `semana1/async_data_fetcher.py`.

| Archivo | Temp. | Modelo que respondió | Complejidad | Nº mejoras | Nº bugs | ¿Inventó algo? | Nota |
|---|:---:|---|:---:|:---:|:---:|:---:|---|
| miniCRUD_API.py | 0.2 | gemini-3-flash-preview | low | 5 | 4 | Parcial | Acierta en los dos bugs reales: `DELETE` lanza `KeyError` (500 en vez de 404) y `PUT` crea la tarea si no existe. Los otros dos son exagerados: la "concurrencia" en `tasks_db` y que `DELETE` devuelva 200 son decisiones de diseño, no bugs. |
| miniCRUD_API.py | 0.8 | gemini-flash-lite-latest | low | 3 | 2 | No | Solo los dos bugs reales. Mejoras concretas (`TaskCreate`, `response_model` en `PUT`). |
| chatbot.py | 0.2 | gemini-flash-lite-latest | low | 3 | 2 | Sí | Dice que `history.pop()` puede romper la alternancia user/assistant: falso, solo quita el mensaje que acaba de añadir. La mejora de capturar `AuthenticationError` sí es real. |
| chatbot.py | 0.8 | gemini-3-flash-preview | low | 4 | 3 | Sí | Afirma que `gemini-3.8-flash` "no es un modelo real" y que dará 404, y propone `gemini-1.5-flash`: conocimiento desactualizado, el modelo existe (falla por 503/429, no por 404). Acierta en que un 401 no está controlado. |
| async_data_fetcher.py | 0.2 | gemini-flash-lite-latest | low | 3 | 2 | Parcial | Dice que si una tarea de `gather` falla "las demás se cancelan": no es así, `gather` propaga la primera excepción y las otras siguen. Los dos bugs son hipotéticos: los datos son simulados y nunca fallan. |
| async_data_fetcher.py | 0.8 | gemini-3-flash-preview | low | 5 | 2 | No | Los mismos dos bugs hipotéticos, bien explicados. Más mejoras, algunas genéricas (`logging`, timeouts en una simulación). |

## Conclusiones
- **Con 0.2:** encuentra los bugs reales de forma estable y da más detalle. Aun así exageró o se equivocó en 3 de 3 archivos en algún punto: temperatura baja no significa que no invente.
- **Con 0.8:** respuestas algo más variadas y con más mejoras genéricas. La invención más grave (decir que mi modelo no existe) salió con 0.8.
- **Lo más importante:** la complejidad (`low`) y los bugs reales salen igual con las dos temperaturas. Lo que cambia es lo que añade alrededor, y ahí es donde inventa.
- **Ojo con la comparación:** `gemini-3.8-flash` estuvo caído (503/429) en todas las ejecuciones, así que cada una la respondió un modelo de respaldo distinto. Parte de la diferencia es del modelo, no de la temperatura. Para una comparación limpia hay que fijar el modelo, y con una sola ejecución por caso no se puede sacar una conclusión firme.
- **Usaría 0.2** para análisis de código y extracción de datos, porque quiero la misma respuesta cada vez y que se ciña al código. Usaría 0.8 para generar ideas o textos, donde la variedad es útil.
