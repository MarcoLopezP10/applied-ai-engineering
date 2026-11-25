# Semana 5 · 23–29 nov · Prompt engineering y arranque

[← Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 6 →](semana-06.md)

🎯 **Objetivo:** un analizador de código que devuelve siempre una respuesta estructurada y válida, tus primeros 2 problemas de algoritmos y la ola 1 de candidaturas en marcha.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 24 | 1 h | Técnico | Code Analyzer: código base + validación con reintento |
| Miércoles 25 | 1 h | Algoritmos | Contains Duplicate y Valid Anagram |
| Jueves 26 | 1 h | Técnico | Probarlo con tu código y comparar temperaturas |
| Sábado 28 | 1,5 h | Técnico + carrera | Prompt library (30 min) + feedback, Revolut y 2 ofertas (1 h) |
| Domingo 29 | 15 min | Cierre | README, log, commit y PR |

**Ya hecho:** la tabla de `practice/algoritmos/README.md` y el renombrado del repo.

### 📖 Qué vas a aprender

- **Prompt engineering:** escribir instrucciones para que el modelo haga lo que quieres de forma repetible. Las 5 técnicas básicas son:
    - **Zero-shot:** pedir la tarea sin ejemplos.
    - **Few-shot:** dar 2–5 ejemplos de entrada y salida antes de la tarea. Sirve sobre todo para fijar el formato.
    - **Chain of thought:** pedir que razone por pasos antes de responder. Mejora tareas con varios pasos.
    - **Rol:** decirle quién es ("ingeniero senior de Python"). Cambia el tono y el nivel de detalle.
    - **Salida estructurada:** exigir un formato exacto (JSON), para que tu código pueda leer la respuesta.
- **Validación con Pydantic:** un modelo de lenguaje no garantiza nada. Defines con una clase qué tiene que devolver, y si no cumple, lo detectas y le pides que lo corrija.
- **Temperatura:** controla cuánto varía la respuesta. Baja (0–0.3) da respuestas más estables, buenas para extraer y analizar. Alta (0.7–1) da más variedad, para ideas o textos creativos.

---

### Martes 24 · 1 h · Code Analyzer

**Paso 1 · Rama (2 min).** En la terminal de VS Code:

```bash
git checkout main && git pull
git checkout -b semana5-prompt-engineering
mkdir -p practice/semana5
```

**Paso 2 · Código base (15 min).** Crea `practice/semana5/code_analyzer.py` con esto. Léelo entero antes de seguir: cada parte es una técnica de prompting (rol en el system prompt, chain of thought en los pasos numerados y formato JSON fijado).

~~~python
"""Semana 5 · Code Analyzer: analiza código Python y devuelve un análisis estructurado."""
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()  # lee GOOGLE_API_KEY del .env

MODELO = "gemini-3.8-flash"  # el mismo que usas en chatbot.py

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


class CodeAnalysis(BaseModel):
    """Lo que el modelo TIENE que devolver. Si no cumple esto, no vale."""
    complexity: Literal["low", "medium", "high"]
    summary: str = Field(min_length=10)
    improvements: list[str]
    potential_bugs: list[str]


# Técnica 1 · ROL: le decimos quién es y cómo debe responder
SYSTEM_PROMPT = """Eres un ingeniero senior experto en Python.
Analizas código y das feedback concreto y accionable.
Responde SOLO con un objeto JSON válido, sin texto antes ni después."""


def build_user_prompt(code: str) -> str:
    # Técnica 2 · CHAIN OF THOUGHT: pasos numerados para que razone en orden
    # Técnica 3 · SALIDA ESTRUCTURADA: le damos el formato exacto
    return f"""Analiza este código Python:

```python
{code}
```

Piensa paso a paso antes de responder:
1. ¿Qué hace el código?
2. ¿Cuál es su complejidad (low, medium o high)?
3. ¿Qué mejoras concretas propondrías?
4. ¿Qué bugs potenciales ves?

Devuelve exactamente este JSON:
{{"complexity": "low|medium|high", "summary": "...", "improvements": ["..."], "potential_bugs": ["..."]}}"""


def analyze_code(code: str, temperature: float = 0.3) -> CodeAnalysis:
    # TODO (paso 3): escribe aquí la llamada al modelo con validación y reintento
    raise NotImplementedError


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: uv run python practice/semana5/code_analyzer.py <archivo.py> [temperatura]")
        sys.exit(1)
    code = Path(sys.argv[1]).read_text(encoding="utf-8")
    temperature = float(sys.argv[2]) if len(sys.argv) > 2 else 0.3
    analysis = analyze_code(code, temperature)
    print(analysis.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
~~~

**Paso 3 · Escribe tú `analyze_code` (30 min).** Esto es lo que tiene que hacer:

1. Crear la lista `messages` con el system prompt y el prompt de usuario.
2. Repetir como máximo 2 veces:
    - Llamar a `client.chat.completions.create(...)` con `model=MODELO`, `messages`, `temperature` y `response_format={"type": "json_object"}`.
    - Intentar convertir el texto de la respuesta en un `CodeAnalysis` con `CodeAnalysis.model_validate_json(texto)`.
    - Si funciona, devolverlo.
    - Si salta `ValidationError`, añadir a `messages` la respuesta del modelo (`role: "assistant"`) y un mensaje tuyo (`role: "user"`) con el error, pidiéndole que lo corrija.
3. Si tras 2 intentos sigue sin valer, lanzar un `ValueError` con un mensaje claro.

**Por qué así:** un modelo a veces devuelve JSON mal formado o le falta un campo. En producción no se confía en él: se valida y, si falla, se le devuelve el error para que lo corrija. Es el patrón más usado para conseguir salidas estructuradas fiables.

> Si la llamada da error por `response_format`, quítalo: el prompt ya pide JSON y la validación con reintento lo cubre.

<details>
<summary>Solución (ábrela solo si llevas 15 min atascado)</summary>

~~~python
def analyze_code(code: str, temperature: float = 0.3) -> CodeAnalysis:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(code)},
    ]
    for intento in range(2):
        response = client.chat.completions.create(
            model=MODELO,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        texto = response.choices[0].message.content
        try:
            return CodeAnalysis.model_validate_json(texto)
        except ValidationError as error:
            print(f"Intento {intento + 1}: JSON no válido, reintentando...")
            messages.append({"role": "assistant", "content": texto})
            messages.append({
                "role": "user",
                "content": f"Tu JSON no es válido:\n{error}\nCorrígelo y devuelve solo el JSON.",
            })
    raise ValueError("El modelo no devolvió un JSON válido tras 2 intentos")
~~~
</details>

**Paso 4 · Pruébalo (10 min):**

```bash
uv run python practice/semana5/code_analyzer.py practice/semana2/miniCRUD_API.py
```

**Está bien si** imprime un JSON con los 4 campos, `complexity` es `low`, `medium` o `high` y las mejoras se refieren a tu código, no a cosas genéricas.

**Paso 5 · Comprueba que el reintento funciona (5 min).** Añade a `CodeAnalysis` un campo que el prompt no pide, por ejemplo `score: int`. Vuelve a ejecutarlo: deberías ver "Intento 1: JSON no válido, reintentando..." y que el segundo intento lo arregla. Después **borra ese campo**.

**Paso 6 · Guarda (2 min):**

```bash
git add practice/semana5/code_analyzer.py
git commit -m "Semana 5: code analyzer con validación y reintento"
```

---

### Miércoles 25 · 1 h · Algoritmos

1. Entra en [neetcode.io](https://neetcode.io/roadmap) → NeetCode 150 → **Arrays & Hashing** → **Contains Duplicate**.
2. Pon un cronómetro de 25 minutos y resuélvelo en el editor de NeetCode, sin ayuda.
    - Si sale: mira igualmente la solución en vídeo para ver si había una forma mejor.
    - Si no sale a los 25 minutos: mira la solución, entiéndela, cierra la pestaña y escríbela tú sin mirar.
3. Guárdalo en `practice/algoritmos/contains_duplicate.py` con este formato (la función la escribes tú):

    ~~~python
    """
    Contains Duplicate · NeetCode 150 · Arrays & Hashing
    Patrón: (escribe aquí la idea clave en una línea)
    Complejidad: O(?) tiempo, O(?) espacio
    """


    def contains_duplicate(nums: list[int]) -> bool:
        ...


    if __name__ == "__main__":
        assert contains_duplicate([1, 2, 3, 1]) is True
        assert contains_duplicate([1, 2, 3, 4]) is False
        print("OK")
    ~~~

4. Comprueba con `uv run python practice/algoritmos/contains_duplicate.py`, que debe imprimir `OK`.
5. Repite con **Valid Anagram** en `practice/algoritmos/valid_anagram.py`, con estas pruebas:

    ~~~python
    assert valid_anagram("anagram", "nagaram") is True
    assert valid_anagram("rat", "car") is False
    ~~~

6. Añade una fila por problema en `practice/algoritmos/README.md`:
    - **Tiempo:** minutos que tardaste
    - **¿Solo?:** sí o no
    - **Qué fallé:** una línea, o "nada"
7. Guarda:

    ```bash
    git add practice/algoritmos
    git commit -m "Algoritmos: Contains Duplicate y Valid Anagram"
    ```

---

### Jueves 26 · 1 h · Probar con tu código y comparar temperaturas

1. Ejecuta el analizador con 3 archivos tuyos, cada uno con temperatura 0.2 y 0.8 (6 ejecuciones):

    ```bash
    uv run python practice/semana5/code_analyzer.py practice/semana2/miniCRUD_API.py 0.2
    uv run python practice/semana5/code_analyzer.py practice/semana2/miniCRUD_API.py 0.8
    uv run python practice/semana5/code_analyzer.py practice/semana4/chatbot.py 0.2
    uv run python practice/semana5/code_analyzer.py practice/semana4/chatbot.py 0.8
    ```

    El tercero es un archivo de tu PSO. Si no está en este repo, cópialo antes a `practice/semana5/ejemplos/` y ejecútalo desde ahí.

2. Crea `practice/semana5/resultados.md` y rellénalo:

    ```markdown
    # Resultados: Code Analyzer

    | Archivo | Temp. | Complejidad | Nº mejoras | Nº bugs | ¿Inventó algo? | Nota |
    |---|:---:|:---:|:---:|:---:|:---:|---|
    | miniCRUD_API.py | 0.2 | | | | | |
    | miniCRUD_API.py | 0.8 | | | | | |
    | chatbot.py | 0.2 | | | | | |
    | chatbot.py | 0.8 | | | | | |
    | (PSO) | 0.2 | | | | | |
    | (PSO) | 0.8 | | | | | |

    ## Conclusiones
    - Con 0.2:
    - Con 0.8:
    - Usaría 0.2 / 0.8 para… porque…
    ```

    **"¿Inventó algo?"** significa si señala un bug que en realidad no existe. Compruébalo leyendo tu código. Es la base de las evals que harás en enero.

3. Guarda:

    ```bash
    git add practice/semana5
    git commit -m "Semana 5: comparación de temperaturas"
    ```

---

### Sábado 28 · 1,5 h

**Técnico, 30 min · Prompt library.** Crea `practice/semana5/prompt_library.md`. El analizador ya usa 3 técnicas (rol, chain of thought y JSON), así que solo tienes que probar dos nuevas, zero-shot y few-shot, con `chatbot.py`:

1. **Zero-shot:** pide "Clasifica el sentimiento de esta reseña como positivo, negativo o neutro: «La entrega llegó tarde pero el producto es genial»". Repítelo 3 veces y fíjate si el formato de la respuesta cambia.
2. **Few-shot:** la misma petición, pero con 3 ejemplos antes (una reseña y su etiqueta, una línea cada uno). Fíjate en si ahora el formato es siempre igual.

Plantilla para cada una de las 5 técnicas:

```markdown
## Few-shot
**Qué es:** (una línea)
**Cuándo usarla:** (una línea)
**Prompt que funcionó:** (el prompt)
**Prompt que no funcionó:** (el prompt)
**Por qué:** (una línea)
```

Para rol, chain of thought y JSON, usa como "prompt que funcionó" los de tu `code_analyzer.py`. Como "prompt que no funcionó", una versión sin esa técnica.

**Carrera, 1 h:**

1. **Feedback (15 min).** Responde al último correo del recruiter de Deloitte, y al de Amazon si te escribió una persona (si fue un correo automático, sáltalo):
    > Hola [nombre], gracias por la oportunidad de participar en el proceso. Me ayudaría mucho saber en qué debería mejorar de cara a futuras oportunidades; cualquier comentario, aunque sea breve, me será muy útil. Un saludo, Marco
2. **Revolut (5 min).** Entra en el portal desde el que aplicaste y comprueba que la candidatura sigue activa. No hay nada más que hacer.
3. **2 ofertas de la ola 1 (40 min).** Revisa si siguen abiertas estas, en su página de empleo: QuantumBlack (McKinsey), Palantir (Forward Deployed Engineer), Oliver Wyman, Microsoft y BCG X. Elige las 2 que mejor encajen y apunta en el Application Tracker de tu Excel: empresa, puesto, enlace, fecha de cierre y estado "Por enviar". Se envían la semana 6.

---

### Domingo 29 · 15 min · Cierre

1. En `practice/README.md`, sustituye "In progress." de la semana 5 por:

    ```markdown
    - [`code_analyzer.py`](semana5/code_analyzer.py): analyzes Python code and returns a validated `CodeAnalysis` object (Pydantic). Uses role prompting, chain of thought and JSON output; if validation fails, it retries once with the error message.
    - [`resultados.md`](semana5/resultados.md): comparison of temperature 0.2 vs 0.8 on three of my own files.
    - [`prompt_library.md`](semana5/prompt_library.md): five prompting techniques with examples that worked and failed.
    ```

2. Rellena tu entrada en `resources/log-semanal.md`.
3. En Claude Code:

    ```
    Cerramos la semana 5. Revisa que el checklist esté cumplido y dime qué falta.
    Luego haz commit de lo que quede, push de semana5-prompt-engineering, abre la PR,
    mergéala con gh pr merge --merge --delete-branch y deja main al día.
    ```

4. Lee la [semana 6](semana-06.md).

---

📦 **Entregable:** `practice/semana5/` (`code_analyzer.py`, `resultados.md`, `prompt_library.md`) + 2 problemas en `practice/algoritmos/`.

✅ **Checklist**
- [ ] El analizador devuelve siempre un `CodeAnalysis` válido
- [ ] He visto el reintento funcionar (paso 5) y he borrado el campo de prueba
- [ ] Tabla de temperaturas con conclusiones
- [ ] Prompt library con 5 técnicas
- [ ] 2 problemas resueltos y anotados
- [ ] Feedback pedido, Revolut revisado y 2 ofertas apuntadas
- [ ] Log y PR de la semana


---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `AuthenticationError` o 401 | El `.env` no está en la raíz del repo o la variable no se llama `GOOGLE_API_KEY`. Comprueba con `cat .env` (sin enseñárselo a nadie). |
| `NotFoundError` con el modelo | El nombre del modelo ha cambiado. Copia el que funciona en `practice/semana4/chatbot.py`. |
| 429 o 503 | Cuota agotada o modelo saturado. Espera un minuto o cambia `MODELO` por uno de respaldo de tu `chatbot.py`. |
| `ModuleNotFoundError: pydantic` | Ejecuta `uv add pydantic` en la raíz del repo. |
| El JSON llega con ```` ```json ```` alrededor | Es habitual sin `response_format`. Tu reintento lo arregla; si pasa siempre, quita las comillas de código antes de validar con `texto.strip().removeprefix("```json").removesuffix("```")`. |
