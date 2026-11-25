# Semana 7 · 7–13 dic · CLI Assistant (2/2): cerrar y publicar

[← Semana 6](semana-06.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 8 →](semana-08.md)

🎯 **Objetivo:** dejar el CLI Assistant terminado y presentable: recuerda la conversación, falla con mensajes claros, tiene tests que no gastan API y un README con demo. Es tu primer proyecto del portfolio.

> **Tiempo cerrado:** si las entregas del máster aprietan, el domingo se publica con lo que haya. Mejor un proyecto pequeño y terminado que uno grande a medias.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 8 | 1 h | Técnico | Historial persistente, `--reset` y configuración |
| Miércoles 9 | 1 h | Algoritmos | Top K Frequent Elements y Valid Palindrome |
| Jueves 10 | 1 h | Técnico | Tests con el LLM simulado |
| Sábado 12 | 1,5 h | Técnico + carrera | README y GIF (30 min) + 1 candidatura y LinkedIn (1 h) |
| Domingo 13 | 15 min | Cierre | Log, PR y enlazar el proyecto en el README principal |

---

### 📖 Qué vas a aprender

- **Estado persistente:** guardar la conversación en un archivo JSON para retomarla. Es la versión mínima de la "memoria" de los agentes.
- **Configuración con `pydantic-settings`:** las variables de entorno se leen y validan con una clase. Si falta la API key, el programa lo dice claramente al arrancar, en vez de fallar con un error raro en mitad de una llamada.
- **Tests con mocks:** los tests **no llaman a la API**, porque gastarían cuota, serían lentos y cada vez darían una respuesta distinta. Sustituyes la función que llama al modelo por una falsa que devuelve lo que tú decides, y compruebas que tu lógica hace lo correcto con esa respuesta.
- **README de proyecto:** es lo primero (y a veces lo único) que mira un recruiter técnico.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana7-cli-final
cd projects/01-cli-ai-assistant
uv add pydantic-settings
```

---

### Martes 8 · 1 h · Historial, `--reset` y configuración

**Paso 1 · Configuración (20 min).** Crea `src/cli_assistant/config.py`:

~~~python
"""Configuración leída del .env y validada al arrancar."""
from functools import lru_cache

from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv(usecwd=True), extra="ignore")

    google_api_key: str  # obligatoria: sin ella no arranca
    modelos: list[str] = ["gemini-3.8-flash", "gemini-flash-lite-latest"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
~~~

Cambia `llm.py` para que use la configuración y cree el cliente solo cuando haga falta (así los tests no necesitan una API key real):

~~~python
"""Cliente de Gemini (a través del SDK de OpenAI) con modelos de respaldo."""
from functools import lru_cache

from openai import APITimeoutError, InternalServerError, OpenAI, RateLimitError

from cli_assistant.config import get_settings

ERRORES_RECUPERABLES = (InternalServerError, RateLimitError, APITimeoutError)


@lru_cache
def get_client() -> OpenAI:
    return OpenAI(
        api_key=get_settings().google_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        max_retries=1,
        timeout=30,
    )


def completar(messages: list[dict], tools: list[dict] | None = None, stream: bool = False):
    """Llama al primer modelo disponible y devuelve la respuesta de la API."""
    ultimo_error = None
    for modelo in get_settings().modelos:
        try:
            kwargs = {"model": modelo, "messages": messages, "stream": stream}
            if tools:
                kwargs["tools"] = tools
            return get_client().chat.completions.create(**kwargs)
        except ERRORES_RECUPERABLES as error:
            ultimo_error = error
    raise RuntimeError(f"Ningún modelo disponible ahora mismo: {ultimo_error}")
~~~

**Paso 2 · Historial persistente (30 min).** Crea `src/cli_assistant/historial.py` y escribe tú las dos funciones:

~~~python
"""Guarda y recupera la conversación entre sesiones."""
import json
from pathlib import Path

RUTA = Path.home() / ".cli_assistant" / "history.json"


def cargar(system_prompt: str) -> list[dict]:
    # TODO: si RUTA existe, devuelve la lista guardada.
    #       Si no existe, devuelve [{"role": "system", "content": system_prompt}].
    raise NotImplementedError


def guardar(historial: list[dict]) -> None:
    # TODO: crea la carpeta si no existe (RUTA.parent.mkdir(parents=True, exist_ok=True))
    #       y escribe el historial como JSON con indent=2 y ensure_ascii=False.
    raise NotImplementedError


def borrar() -> None:
    RUTA.unlink(missing_ok=True)
~~~

<details>
<summary>Solución</summary>

~~~python
def cargar(system_prompt: str) -> list[dict]:
    if RUTA.exists():
        return json.loads(RUTA.read_text(encoding="utf-8"))
    return [{"role": "system", "content": system_prompt}]


def guardar(historial: list[dict]) -> None:
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    RUTA.write_text(json.dumps(historial, indent=2, ensure_ascii=False), encoding="utf-8")
~~~
</details>

**Paso 3 · Conectarlo en `main.py` (10 min).** Sustituye la función `chat` por esta versión. Fíjate en la opción `--reset` y en el error claro si falta la API key:

~~~python
from pydantic import ValidationError

from cli_assistant import historial as hist
from cli_assistant.config import get_settings


@app.command()
def chat(reset: bool = typer.Option(False, "--reset", help="Empieza una conversación nueva.")) -> None:
    """Conversación con el asistente. Escribe 'exit' para salir."""
    try:
        get_settings()
    except ValidationError:
        console.print("[red]Falta GOOGLE_API_KEY. Añádela al archivo .env de la raíz del repo.[/red]")
        raise typer.Exit(code=1)

    if reset:
        hist.borrar()
    historial = hist.cargar(SYSTEM_PROMPT)
    console.print("[bold green]Asistente[/bold green] · escribe 'exit' para salir\n")
    while True:
        pregunta = console.input("[bold]Tú:[/bold] ").strip()
        if pregunta.lower() in {"exit", "salir"}:
            break
        historial.append({"role": "user", "content": pregunta})
        responder(historial)
        hist.guardar(historial)
        console.print()
~~~

**Comprueba:**

1. Desde la raíz del repo, `uv run --project projects/01-cli-ai-assistant asistente chat`. Di "me llamo Marco" y sal.
2. Vuelve a entrar y pregunta "¿cómo me llamo?" → debe acordarse.
3. Entra con `... asistente chat --reset` y pregunta lo mismo → ya no lo sabe.

```bash
git add -A && git commit -m "CLI: historial persistente, --reset y configuración validada"
```

---

### Miércoles 9 · 1 h · Algoritmos

**Top K Frequent Elements** (Medium) → `practice/algoritmos/top_k_frequent.py`

~~~python
"""
Top K Frequent Elements · NeetCode 150 · Arrays & Hashing
Patrón:
Complejidad: O(?) tiempo, O(?) espacio
"""


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    ...


if __name__ == "__main__":
    assert sorted(top_k_frequent([1, 1, 1, 2, 2, 3], 2)) == [1, 2]
    assert top_k_frequent([1], 1) == [1]
    print("OK")
~~~

<details>
<summary>Pista</summary>
Primero cuenta cuántas veces aparece cada número. Después, la solución O(n log n) ordena por frecuencia. La O(n) usa "cubos": una lista donde la posición i guarda los números que aparecen i veces.
</details>

**Valid Palindrome** (Easy, patrón Two Pointers) → `practice/algoritmos/valid_palindrome.py`

~~~python
def valid_palindrome(s: str) -> bool:
    ...


if __name__ == "__main__":
    assert valid_palindrome("A man, a plan, a canal: Panama") is True
    assert valid_palindrome("race a car") is False
    assert valid_palindrome(" ") is True
    print("OK")
~~~

<details>
<summary>Pista</summary>
Un puntero al principio y otro al final. Sáltate lo que no sea letra o número (`str.isalnum`) y compara en minúsculas.
</details>

---

### Jueves 10 · 1 h · Tests con el LLM simulado

**Paso 1 · Ayudantes de test (15 min).** Crea `tests/conftest.py`. Los objetos `SimpleNamespace` imitan la forma de los trozos que devuelve la API en streaming, sin llamarla:

~~~python
"""Utilidades compartidas por los tests: imitan las respuestas de la API."""
import os
from types import SimpleNamespace as NS

os.environ.setdefault("GOOGLE_API_KEY", "clave-de-test")  # los tests nunca usan la real


def chunk_texto(texto: str):
    return NS(choices=[NS(delta=NS(content=texto, tool_calls=None))])


def chunk_llamada(id: str, nombre: str, argumentos: str, index: int = 0):
    llamada = NS(index=index, id=id, function=NS(name=nombre, arguments=argumentos))
    return NS(choices=[NS(delta=NS(content=None, tool_calls=[llamada]))])
~~~

**Paso 2 · Tests de herramientas (15 min).** Crea `tests/test_tools.py`:

~~~python
from cli_assistant.tools import ejecutar, leer_archivo


def test_leer_archivo_dentro_de_la_carpeta(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "nota.txt").write_text("hola")
    assert leer_archivo("nota.txt") == "hola"


def test_leer_archivo_fuera_de_la_carpeta_se_bloquea(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert "solo puedo leer" in leer_archivo("../../etc/passwd")


def test_herramienta_desconocida():
    assert "desconocida" in ejecutar("borrar_todo", "{}")


def test_argumentos_mal_formados_no_rompen_el_programa():
    assert ejecutar("leer_archivo", "esto no es json").startswith("Error")
~~~

**Paso 3 · Tests del bucle (25 min).** Crea `tests/test_responder.py`. Escribe tú el tercer test, siguiendo el patrón de los dos primeros:

~~~python
from conftest import chunk_llamada, chunk_texto

from cli_assistant import main


def test_responde_sin_herramientas(monkeypatch):
    monkeypatch.setattr(main, "completar", lambda *a, **k: iter([chunk_texto("Hola "), chunk_texto("Marco")]))
    historial = [{"role": "user", "content": "hola"}]
    assert main.responder(historial) == "Hola Marco"
    assert historial[-1] == {"role": "assistant", "content": "Hola Marco"}


def test_usa_una_herramienta_y_luego_responde(monkeypatch):
    respuestas = iter([
        [chunk_llamada("c1", "hora_actual", "{}")],  # 1.ª llamada: pide la herramienta
        [chunk_texto("Son las 18:00")],              # 2.ª llamada: responde
    ])
    monkeypatch.setattr(main, "completar", lambda *a, **k: iter(next(respuestas)))
    historial = [{"role": "user", "content": "¿qué hora es?"}]
    assert main.responder(historial) == "Son las 18:00"
    mensajes_tool = [m for m in historial if m["role"] == "tool"]
    assert len(mensajes_tool) == 1 and mensajes_tool[0]["tool_call_id"] == "c1"


def test_para_tras_max_vueltas(monkeypatch):
    # TODO: haz que completar SIEMPRE pida una herramienta
    #       y comprueba que responder devuelve el mensaje de "demasiados pasos".
    ...
~~~

<details>
<summary>Solución del tercer test</summary>

~~~python
def test_para_tras_max_vueltas(monkeypatch):
    monkeypatch.setattr(main, "completar", lambda *a, **k: iter([chunk_llamada("c", "hora_actual", "{}")]))
    assert "demasiados pasos" in main.responder([{"role": "user", "content": "x"}])
~~~
</details>

**Ejecuta:**

```bash
uv run pytest -v
```

**Está bien si** salen 7 tests en verde. Si ves "PASSED" sin haber tocado Internet, ese es el objetivo.

```bash
git add -A && git commit -m "CLI: tests de herramientas y del bucle con el LLM simulado"
```

---

### Sábado 12 · 1,5 h

**Técnico, 30 min · README y GIF.**

1. Graba un GIF de 20–30 segundos con [Kap](https://getkap.co) (gratis para Mac): pregunta la hora, pide un resumen de un archivo y sal. Guárdalo como `projects/01-cli-ai-assistant/docs/demo.gif`.
2. Crea `projects/01-cli-ai-assistant/README.md` con esta plantilla (en inglés, para recruiters):

```markdown
# CLI AI Assistant

Terminal assistant powered by an LLM (Gemini through the OpenAI SDK) that decides when to use local tools.

![demo](docs/demo.gif)

## What it does
- Chat with streaming responses and persistent history (`--reset` to start over)
- Tool calling: reads files from the current folder (sandboxed) and tells the time
- Falls back to another model when one is overloaded (503), rate-limited (429) or times out

## Architecture
`main.py` (CLI + tool-calling loop) → `llm.py` (client + fallback) → `tools.py` (tool schemas + execution)

## Decisions
- **Tools never raise:** errors are returned to the model as text so it can recover.
- **File access is sandboxed** to the working directory.
- **Tests mock the LLM**, so they are fast, free and deterministic.

## What I'd improve
(1–2 lines)

## Run it
    uv sync
    uv run asistente chat
```

**Carrera, 1 h:**

1. **1 candidatura** (30 min) de la ola 1, con el mismo método de la semana 6.
2. **Titular de LinkedIn** (15 min): *Computer Engineer · MSc Business Analytics & Data Science @ IE · Building applied AI (RAG, agents) with Python*.
3. **Destacado de LinkedIn** (15 min): añade el repo del CLI con el GIF como imagen.

---

### Domingo 13 · 15 min · Cierre

1. En el `README.md` principal, cambia el estado del proyecto 01 a **Done**.
2. Añade a `practice/README.md` la línea de la semana 7.
3. Rellena el log semanal.
4. En Claude Code:
    ```
    Cerramos la semana 7. Revisa el checklist de resources/semanas/semana-07.md,
    ejecuta los tests del CLI y dime qué falta. Luego commit, push de
    semana7-cli-final, PR, mergea y deja main al día.
    ```

---

📦 **Entregable:** `projects/01-cli-ai-assistant` terminado, con tests, README y GIF.

✅ **Checklist**
- [ ] Recuerda la conversación entre sesiones y `--reset` la borra
- [ ] Sin API key, el mensaje de error es claro
- [ ] 7 tests en verde sin llamar a la API
- [ ] README con GIF, decisiones y cómo ejecutarlo
- [ ] Proyecto marcado como Done en el README principal
- [ ] 1 candidatura más; titular y destacado de LinkedIn

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `ImportError: conftest` en los tests | Ejecuta `uv run pytest` desde `projects/01-cli-ai-assistant`. Si persiste, crea un archivo vacío `tests/__init__.py`. |
| Los tests llaman a la API de verdad | El `monkeypatch.setattr` debe apuntar a `main.completar` (donde se usa), no a `llm.completar`. |
| `TypeError: Object of type ... is not JSON serializable` al guardar | Algún mensaje guarda un objeto de la API en vez de un diccionario. Revisa que añades diccionarios al historial. |
| El historial crece mucho y las respuestas se vuelven lentas | Normal con historial infinito. Mejora opcional: guardar solo los últimos 20 mensajes (más el system). |
