# Prompt library

Cinco técnicas básicas de prompting, cada una con un prompt que funcionó y otro que no. Zero-shot y few-shot los probé con `chat()` de `semana4/chatbot.py` (3 veces cada uno, historial limpio). Rol, chain of thought y JSON los probé con `code_analyzer.py` sobre `semana2/miniCRUD_API.py`, quitando una técnica cada vez.

## Zero-shot
**Qué es:** pedir la tarea directamente, sin ejemplos.
**Cuándo usarla:** tareas sencillas o exploratorias donde el formato de la respuesta no importa.
**Prompt que funcionó:** `Clasifica el sentimiento de esta reseña como positivo, negativo o neutro: «La entrega llegó tarde pero el producto es genial»` → las 3 veces respondió "Neutro (o mixto)" con una explicación razonable.
**Prompt que no funcionó:** el mismo, si lo que necesito es una etiqueta que lea mi código. Responde "**Neutro** (o mixto), ya que combina…": a veces en negrita y a veces no, con una etiqueta que no pedí ("mixto") y una frase detrás.
**Por qué:** sin ejemplos, el modelo decide él solo el formato y el criterio. La respuesta es correcta para una persona, pero no se puede parsear.

## Few-shot
**Qué es:** dar 2–5 ejemplos de entrada y salida antes de la tarea.
**Cuándo usarla:** cuando el formato de salida tiene que ser exacto y repetible, o para fijar un criterio dudoso.
**Prompt que funcionó:**
```
Clasifica el sentimiento de cada reseña como positivo, negativo o neutro.

Reseña: «Me encanta, lo volvería a comprar» → positivo
Reseña: «Llegó roto y nadie me responde» → negativo
Reseña: «Cumple, sin más» → neutro
Reseña: «La entrega llegó tarde pero el producto es genial» →
```
→ las 3 veces respondió exactamente `positivo`: una palabra, en minúscula y sin explicación.
**Prompt que no funcionó:** la versión zero-shot de arriba.
**Por qué:** los ejemplos fijan el formato mejor que cualquier instrucción. Ojo: también cambiaron la etiqueta (de "neutro" a "positivo"). Los ejemplos influyen en el criterio, no solo en el formato, así que hay que elegirlos bien.

## Rol
**Qué es:** decirle al modelo quién es y cómo debe responder, en el system prompt.
**Cuándo usarla:** para fijar el nivel técnico, el tono y el tipo de feedback.
**Prompt que funcionó:** el `SYSTEM_PROMPT` de `code_analyzer.py`: `Eres un ingeniero senior experto en Python. Analizas código y das feedback concreto y accionable. Responde SOLO con un objeto JSON válido, sin texto antes ni después.`
**Prompt que no funcionó:** el mismo user prompt sin system prompt. Devolvió un JSON válido y muy parecido: los mismos bugs, con algo menos de detalle en las mejoras.
**Por qué:** en esta tarea apenas se nota, porque el user prompt ya es muy específico. El rol pesa más cuando la petición es abierta (en la semana 4, los asistentes formal, casual y técnico cambiaban mucho el tono).

## Chain of thought
**Qué es:** pedir que razone por pasos antes de responder.
**Cuándo usarla:** tareas con varios pasos (analizar, decidir, justificar) o con cálculos.
**Prompt que funcionó:** los 4 pasos numerados de `build_user_prompt` (qué hace, complejidad, mejoras y bugs).
**Prompt que no funcionó:** el mismo prompt sin los pasos. También devolvió un JSON válido y encontró los dos bugs reales, pero el resumen fue más pobre ("Una API CRUD básica…") y una de las mejoras era genérica (pasar a `async def` sin motivo).
**Por qué:** con salida JSON el modelo no escribe su razonamiento, así que los pasos funcionan más como una lista de qué mirar que como razonamiento real. En un código tan corto la diferencia es pequeña.

## Salida estructurada (JSON)
**Qué es:** exigir un formato exacto, en este caso un JSON con los campos de `CodeAnalysis`, para que el código pueda leer la respuesta.
**Cuándo usarla:** siempre que la respuesta la vaya a procesar un programa y no una persona.
**Prompt que funcionó:** el JSON de ejemplo al final de `build_user_prompt` + `response_format={"type": "json_object"}` + validación con Pydantic y reintento → `CodeAnalysis` válido en todas las ejecuciones.
**Prompt que no funcionó:** `Analiza este código Python y dime complejidad, mejoras y bugs:` sin formato. Devolvió un análisis en Markdown ("### 1. Bugs…") que no pasa la validación.
**Por qué:** es la técnica que más cambia el resultado. Sin ella el contenido es bueno, pero el programa no puede usarlo. Aun con ella, el modelo no garantiza nada, por eso se valida con Pydantic.
