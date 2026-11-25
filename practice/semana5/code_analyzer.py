"""Semana 5 · Code Analyzer: analiza código Python y devuelve un análisis estructurado."""
import os
import sys
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI
from pydantic import BaseModel, Field, ValidationError

load_dotenv()  # lee GOOGLE_API_KEY del .env

# Igual que en chatbot.py: el principal primero, los demás de respaldo si está saturado
MODELOS = ["gemini-3.8-flash", "gemini-flash-lite-latest", "gemini-3-flash-preview"]
MAX_INTENTOS = 2

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    max_retries=1,
    timeout=60,
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


def call_model(messages: list[dict], temperature: float) -> str:
    """Llama al primer modelo disponible. Si uno da 503/429 o no responde, prueba el siguiente."""
    for modelo in MODELOS:
        try:
            response = client.chat.completions.create(
                model=modelo,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except (APIStatusError, APIConnectionError) as e:
            print(f"{modelo} no disponible ({type(e).__name__}), probando otro...", file=sys.stderr)
    raise RuntimeError("Ningún modelo está disponible ahora mismo. Espera un minuto.")


def analyze_code(code: str, temperature: float = 0.3) -> CodeAnalysis:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(code)},
    ]
    for intento in range(MAX_INTENTOS):
        texto = call_model(messages, temperature)
        try:
            return CodeAnalysis.model_validate_json(texto)
        except ValidationError as error:
            print(f"Intento {intento + 1}: JSON no válido, reintentando...", file=sys.stderr)
            # Le devolvemos su propia respuesta y el error para que lo corrija
            messages.append({"role": "assistant", "content": texto})
            messages.append({
                "role": "user",
                "content": f"Tu JSON no es válido:\n{error}\nCorrígelo y devuelve solo el JSON.",
            })
    raise ValueError(f"El modelo no devolvió un JSON válido tras {MAX_INTENTOS} intentos")


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
