# Semana 6 · 30 nov – 6 dic · Tool calling + CLI Assistant (1/2)

[← Semana 5](semana-05.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 7 →](semana-07.md)

🎯 **Objetivo:** un asistente de terminal que conversa contigo, decide cuándo usar herramientas tuyas (leer un archivo, saber la hora) y muestra la respuesta en streaming. Además, enviar 2 candidaturas de la ola 1.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 1 | 1 h | Técnico | Estructura del proyecto, cliente del LLM y herramientas |
| Miércoles 2 | 1 h | Algoritmos | Two Sum y Group Anagrams |
| Jueves 3 | 1 h | Técnico | El bucle de tool calling (lo escribes tú) |
| Sábado 5 | 1,5 h | Técnico + carrera | Streaming (30 min) + 2 candidaturas (1 h) |
| Domingo 6 | 15 min | Cierre | Log, commit y PR |

---

### 📖 Qué vas a aprender

**Tool calling (function calling).** El modelo **no ejecuta nada**. Le describes tus funciones (nombre, para qué sirven y qué argumentos aceptan) y, cuando cree que necesita una, en vez de texto te devuelve una petición: "llama a `leer_archivo` con `ruta = 'notas.md'`". Tu código la ejecuta y le devuelve el resultado en un mensaje con `role: "tool"`. Con eso, el modelo escribe la respuesta final.

```
Tú: "¿qué hora es?"
   → modelo: tool_calls = [hora_actual()]          (no responde, pide)
   → tu código ejecuta hora_actual() = "martes 1/12 18:03"
   → mensaje role "tool" con ese resultado
   → modelo: "Son las 18:03 del martes."             (ahora sí responde)
```

Este ciclo de pedir, ejecutar, devolver y responder es **la base de todos los agentes** que harás en abril. Si lo entiendes ahora, LangGraph será fácil.

**Descripción de herramientas.** Se escriben en JSON Schema. La `description` es un prompt más: si es vaga, el modelo no sabrá cuándo usar la herramienta.

**Streaming.** En vez de esperar a la respuesta entera, la API te manda trozos (*chunks*) según los genera. Se nota mucho en un chat: el texto aparece mientras se escribe.

**Typer.** Convierte funciones de Python en comandos de terminal (`asistente chat`) sin escribir tú el *parsing* de argumentos.

---

### Antes de empezar (5 min)

```bash
git checkout main && git pull
git checkout -b semana6-tool-calling
cd projects/01-cli-ai-assistant
git mv test_openai.py ../../practice/semana4/test_gemini_rest.py
```

El último comando mueve tu prueba antigua a la carpeta de la semana 4, que es donde le corresponde.

---

### Martes 1 · 1 h · Estructura, cliente y herramientas

**Paso 1 · Crear el proyecto (10 min).** Dentro de `projects/01-cli-ai-assistant`:

```bash
uv init --package --name cli-assistant .
uv add openai python-dotenv rich typer
uv add --dev pytest
```

`uv init --package` crea `pyproject.toml` y la carpeta `src/cli_assistant/`. Este proyecto tiene sus propias dependencias, separadas de las del repo.

Abre `pyproject.toml` y añade al final:

```toml
[project.scripts]
asistente = "cli_assistant.main:app"
```

Así podrás ejecutar `uv run asistente chat`.

**Paso 2 · Cliente con modelos de respaldo (15 min).** Crea `src/cli_assistant/llm.py`. Es la misma idea que el *fallback* de tu `chatbot.py`, metida en una función reutilizable:

~~~python
"""Cliente de Gemini (a través del SDK de OpenAI) con modelos de respaldo."""
import os

from dotenv import load_dotenv
from openai import APITimeoutError, InternalServerError, OpenAI, RateLimitError

load_dotenv()  # busca el .env subiendo carpetas: encuentra el de la raíz del repo

# Copia aquí los nombres que te funcionan en practice/semana4/chatbot.py
MODELOS = ["gemini-3.8-flash", "gemini-flash-lite-latest"]
ERRORES_RECUPERABLES = (InternalServerError, RateLimitError, APITimeoutError)

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    max_retries=1,
    timeout=30,
)


def completar(messages: list[dict], tools: list[dict] | None = None, stream: bool = False):
    """Llama al primer modelo disponible y devuelve la respuesta de la API."""
    ultimo_error = None
    for modelo in MODELOS:
        try:
            kwargs = {"model": modelo, "messages": messages, "stream": stream}
            if tools:
                kwargs["tools"] = tools
            return client.chat.completions.create(**kwargs)
        except ERRORES_RECUPERABLES as error:
            ultimo_error = error
    raise RuntimeError(f"Ningún modelo disponible ahora mismo: {ultimo_error}")
~~~

**Paso 3 · Herramientas (25 min).** Crea `src/cli_assistant/tools.py`. Fíjate en tres cosas:

- `TOOLS` es lo que **ve el modelo**: nombre, descripción y argumentos.
- `FUNCIONES` es lo que **ejecuta tu código**.
- `leer_archivo` solo lee dentro de la carpeta desde la que lanzas el asistente. Es tu primer *guardrail*: un modelo nunca debe poder leer cualquier archivo de tu ordenador.

~~~python
"""Herramientas que el modelo puede pedir usar."""
import json
from datetime import datetime
from pathlib import Path


def hora_actual() -> str:
    return datetime.now().strftime("%A %d/%m/%Y %H:%M")


def leer_archivo(ruta: str, max_caracteres: int = 8000) -> str:
    base = Path.cwd().resolve()
    archivo = (base / ruta).resolve()
    if not archivo.is_relative_to(base):
        return "Error: solo puedo leer archivos dentro de la carpeta actual."
    if not archivo.is_file():
        return f"Error: no existe el archivo {ruta}"
    return archivo.read_text(encoding="utf-8", errors="replace")[:max_caracteres]


# Lo que ve el modelo (JSON Schema)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "hora_actual",
            "description": "Devuelve la fecha y la hora actuales del ordenador del usuario.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "leer_archivo",
            "description": (
                "Lee un archivo de texto de la carpeta actual y devuelve su contenido "
                "(máximo 8000 caracteres). Úsala cuando el usuario pida resumir, "
                "explicar o revisar un archivo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ruta": {
                        "type": "string",
                        "description": "Ruta relativa, por ejemplo practice/semana2/miniCRUD_API.py",
                    }
                },
                "required": ["ruta"],
            },
        },
    },
]

# Lo que ejecuta tu código
FUNCIONES = {"hora_actual": hora_actual, "leer_archivo": leer_archivo}


def ejecutar(nombre: str, argumentos_json: str) -> str:
    """Ejecuta la herramienta pedida. Nunca lanza excepción: devuelve el error como texto."""
    if nombre not in FUNCIONES:
        return f"Error: herramienta desconocida {nombre}"
    try:
        argumentos = json.loads(argumentos_json or "{}")
        return str(FUNCIONES[nombre](**argumentos))
    except Exception as error:  # el modelo puede mandar argumentos incorrectos
        return f"Error al ejecutar {nombre}: {error}"
~~~

**Por qué `ejecutar` nunca lanza excepción:** si el modelo manda un argumento malo, es mejor devolverle el error como texto. Así puede corregirse en la siguiente vuelta, en lugar de que se caiga tu programa.

**Paso 4 · Comprobar (5 min).** Desde `projects/01-cli-ai-assistant`:

```bash
uv run python -c "from cli_assistant.tools import ejecutar; print(ejecutar('hora_actual', '{}')); print(ejecutar('leer_archivo', '{\"ruta\": \"../../.env\"}'))"
```

**Está bien si** la primera línea es la hora y la segunda es el error "solo puedo leer archivos dentro de la carpeta actual". Tu `.env` está protegido.

```bash
git add -A && git commit -m "CLI: estructura, cliente con fallback y herramientas"
```

---

### Miércoles 2 · 1 h · Algoritmos

Mismo método que la semana 5: 25 minutos con cronómetro, archivo en `practice/algoritmos/` y una fila en el README.

**Two Sum** (Easy) → `practice/algoritmos/two_sum.py`

~~~python
"""
Two Sum · NeetCode 150 · Arrays & Hashing
Patrón:
Complejidad: O(?) tiempo, O(?) espacio
"""


def two_sum(nums: list[int], target: int) -> list[int]:
    ...


if __name__ == "__main__":
    assert sorted(two_sum([2, 7, 11, 15], 9)) == [0, 1]
    assert sorted(two_sum([3, 2, 4], 6)) == [1, 2]
    assert sorted(two_sum([3, 3], 6)) == [0, 1]
    print("OK")
~~~

<details>
<summary>Pista (solo si llevas 15 min)</summary>
Para cada número, ¿qué otro número necesitas? Si guardas en un diccionario los números que ya has visto y su posición, puedes comprobarlo en O(1).
</details>

**Group Anagrams** (tu primer Medium) → `practice/algoritmos/group_anagrams.py`

~~~python
"""
Group Anagrams · NeetCode 150 · Arrays & Hashing
Patrón:
Complejidad: O(?) tiempo, O(?) espacio
"""


def group_anagrams(strs: list[str]) -> list[list[str]]:
    ...


if __name__ == "__main__":
    resultado = group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"])
    normalizado = sorted(sorted(grupo) for grupo in resultado)
    assert normalizado == [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]
    print("OK")
~~~

<details>
<summary>Pista</summary>
Dos anagramas tienen algo idéntico si los transformas de cierta manera. Úsalo como clave de un diccionario.
</details>

```bash
git add practice/algoritmos && git commit -m "Algoritmos: Two Sum y Group Anagrams"
```

---

### Jueves 3 · 1 h · El bucle de tool calling (lo escribes tú)

Crea `src/cli_assistant/main.py` con este esqueleto:

~~~python
"""Asistente de IA en la terminal."""
import typer
from rich.console import Console

from cli_assistant.llm import completar
from cli_assistant.tools import TOOLS, ejecutar

app = typer.Typer(help="Asistente de IA en la terminal.")
console = Console()

SYSTEM_PROMPT = (
    "Eres un asistente útil y conciso para un estudiante de ingeniería. "
    "Usa las herramientas cuando las necesites y no inventes el contenido de archivos."
)
MAX_VUELTAS = 3  # máximo de rondas de herramientas por pregunta


def responder(historial: list[dict]) -> str:
    # TODO: tu bucle de tool calling
    raise NotImplementedError


@app.command()
def chat() -> None:
    """Conversación con el asistente. Escribe 'exit' para salir."""
    historial = [{"role": "system", "content": SYSTEM_PROMPT}]
    console.print("[bold green]Asistente[/bold green] · escribe 'exit' para salir\n")
    while True:
        pregunta = console.input("[bold]Tú:[/bold] ").strip()
        if pregunta.lower() in {"exit", "salir"}:
            break
        historial.append({"role": "user", "content": pregunta})
        respuesta = responder(historial)
        console.print(f"[bold blue]Asistente:[/bold blue] {respuesta}\n")


if __name__ == "__main__":
    app()
~~~

**Lo que tiene que hacer `responder`:**

1. Repetir como máximo `MAX_VUELTAS` veces:
    - Llamar a `completar(historial, tools=TOOLS)` y coger `mensaje = respuesta.choices[0].message`.
    - **Si `mensaje.tool_calls` está vacío:** el modelo ya ha respondido. Añade `{"role": "assistant", "content": mensaje.content}` al historial y devuelve el texto.
    - **Si tiene `tool_calls`:**
        - Añade al historial el mensaje del asistente con sus llamadas: `{"role": "assistant", "content": mensaje.content, "tool_calls": [llamada.model_dump() for llamada in mensaje.tool_calls]}`.
        - Para cada llamada: ejecuta `ejecutar(llamada.function.name, llamada.function.arguments)` y añade `{"role": "tool", "tool_call_id": llamada.id, "content": resultado}`.
        - Imprime en gris qué herramienta se usa, para verlo: `console.print(f"[dim]→ {llamada.function.name}({llamada.function.arguments})[/dim]")`.
2. Si se acaban las vueltas, devolver un mensaje tipo "He necesitado demasiados pasos; reformula la pregunta".

**Por qué el historial guarda también las llamadas:** el modelo no tiene memoria. En cada llamada le mandas toda la conversación, y tiene que ver qué pidió y qué le devolviste para poder responder.

<details>
<summary>Solución (ábrela solo si llevas 20 min atascado)</summary>

~~~python
def responder(historial: list[dict]) -> str:
    for _ in range(MAX_VUELTAS):
        respuesta = completar(historial, tools=TOOLS)
        mensaje = respuesta.choices[0].message
        if not mensaje.tool_calls:
            historial.append({"role": "assistant", "content": mensaje.content})
            return mensaje.content
        historial.append({
            "role": "assistant",
            "content": mensaje.content,
            "tool_calls": [llamada.model_dump() for llamada in mensaje.tool_calls],
        })
        for llamada in mensaje.tool_calls:
            console.print(f"[dim]→ {llamada.function.name}({llamada.function.arguments})[/dim]")
            resultado = ejecutar(llamada.function.name, llamada.function.arguments)
            historial.append({"role": "tool", "tool_call_id": llamada.id, "content": resultado})
    return "He necesitado demasiados pasos; reformula la pregunta."
~~~
</details>

**Pruébalo.** Lanza el asistente **desde la raíz del repo**, para que pueda leer tus archivos:

```bash
cd ../..
uv run --project projects/01-cli-ai-assistant asistente chat
```

Prueba estas tres preguntas:

1. "¿Qué hora es?" → debe salir `→ hora_actual({})`.
2. "Resume practice/semana2/miniCRUD_API.py en 3 puntos" → debe salir `→ leer_archivo(...)` y un resumen correcto.
3. "¿Cuánto es 2+2?" → no debe usar ninguna herramienta.

```bash
git add -A && git commit -m "CLI: bucle de tool calling"
```

---

### Sábado 5 · 1,5 h

**Técnico, 30 min · Streaming.** Ahora la respuesta se mostrará mientras se genera. El reto es que, en streaming, las llamadas a herramientas también llegan a trozos y hay que juntarlas. Esta parte es mecánica, así que aquí tienes el código. Léelo línea a línea y sustituye tu `responder`. Guarda tu versión en un comentario o en el historial de git para compararlas.

~~~python
def responder(historial: list[dict]) -> str:
    for _ in range(MAX_VUELTAS):
        stream = completar(historial, tools=TOOLS, stream=True)
        texto = ""
        llamadas: dict[int, dict] = {}  # posición → {"id", "name", "arguments"}
        console.print("[bold blue]Asistente:[/bold blue] ", end="")
        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:  # un trozo de texto: se imprime al momento
                texto += delta.content
                console.print(delta.content, end="")
            for parcial in delta.tool_calls or []:  # un trozo de una llamada: se acumula
                actual = llamadas.setdefault(parcial.index or 0, {"id": "", "name": "", "arguments": ""})
                if parcial.id:
                    actual["id"] = parcial.id
                if parcial.function and parcial.function.name:
                    actual["name"] += parcial.function.name
                if parcial.function and parcial.function.arguments:
                    actual["arguments"] += parcial.function.arguments
        console.print()
        if not llamadas:
            historial.append({"role": "assistant", "content": texto})
            return texto
        historial.append({
            "role": "assistant",
            "content": texto or None,
            "tool_calls": [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["name"], "arguments": c["arguments"]}}
                for c in llamadas.values()
            ],
        })
        for c in llamadas.values():
            console.print(f"[dim]→ {c['name']}({c['arguments']})[/dim]")
            historial.append({"role": "tool", "tool_call_id": c["id"],
                              "content": ejecutar(c["name"], c["arguments"])})
    return "He necesitado demasiados pasos; reformula la pregunta."
~~~

Como `responder` ya imprime la respuesta, en `chat()` cambia la línea `console.print(f"[bold blue]Asistente:[/bold blue] {respuesta}\n")` por `console.print()`.

> Si Gemini da error al combinar streaming y herramientas, vuelve a tu versión del jueves y anótalo en el README como limitación conocida. Saber decir "esto no funcionaba con este proveedor y lo resolví así" también cuenta en una entrevista.

Repite las 3 preguntas del jueves y haz commit: `git add -A && git commit -m "CLI: respuestas en streaming"`.

**Carrera, 1 h · 2 candidaturas de la ola 1.** Para cada una de las 2 ofertas que apuntaste el sábado pasado:

1. Lee la oferta y subraya 5 palabras clave (por ejemplo LLM, Python, AWS, cliente, agentes).
2. Haz una copia de tu CV con un nombre como `CV_Marco_Lopez_QuantumBlack.docx` y cambia **solo 3 cosas**:
    - El *summary*, para que mencione 2–3 de esas palabras clave.
    - El orden de la línea de skills, poniendo primero lo que piden.
    - Un bullet de proyecto reescrito con su vocabulario.
3. Envíala y apúntala en el Application Tracker: fecha, canal, estado "Enviada" y fecha de follow-up a +10 días.

---

### Domingo 6 · 15 min · Cierre

1. En `practice/README.md` añade:
    ```markdown
    ## Week 6: Tool calling

    - [CLI AI Assistant](../projects/01-cli-ai-assistant): terminal assistant with tool calling (read files safely, current time), model fallback and streaming responses. Project in progress (finished in week 7).
    ```
2. Rellena tu entrada en `resources/log-semanal.md`.
3. En Claude Code:
    ```
    Cerramos la semana 6. Revisa el checklist de resources/semanas/semana-06.md
    y dime qué falta. Luego haz commit de lo que quede, push de semana6-tool-calling,
    abre la PR, mergéala con gh pr merge --merge --delete-branch y deja main al día.
    ```

---

📦 **Entregable:** `projects/01-cli-ai-assistant` con un asistente que conversa en streaming y usa 2 herramientas.

✅ **Checklist**
- [ ] Sé explicar el ciclo pedir → ejecutar → devolver → responder
- [ ] `hora_actual` y `leer_archivo` funcionan desde el chat
- [ ] `leer_archivo` no puede salir de la carpeta actual
- [ ] Respuestas en streaming (o limitación documentada)
- [ ] 2 problemas de algoritmos anotados
- [ ] 2 candidaturas enviadas y en el tracker

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `uv run asistente` dice "command not found" | Falta `[project.scripts]` en el `pyproject.toml` del proyecto, o no ejecutaste `uv sync` después de añadirlo. |
| `ModuleNotFoundError: cli_assistant` | Estás fuera de la carpeta del proyecto. Usa `uv run --project projects/01-cli-ai-assistant ...` desde la raíz. |
| El modelo nunca usa las herramientas | Mejora la `description` de la herramienta y el system prompt. Prueba preguntas explícitas ("lee el archivo X"). |
| Error 400 al devolver el resultado de una herramienta | El `tool_call_id` no coincide con el `id` de la llamada, o falta el mensaje del asistente con `tool_calls` antes de los mensajes `tool`. |
| `leer_archivo` no encuentra el archivo | La ruta es relativa a la carpeta desde la que lanzas el asistente: lánzalo desde la raíz del repo. |
