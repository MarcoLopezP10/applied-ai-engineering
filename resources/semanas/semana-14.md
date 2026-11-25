# Semana 14 · 25–31 ene · Experimento: troceado y modelos

[← Semana 13](semana-13.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 15 →](semana-15.md)

🎯 **Objetivo:** tomar dos decisiones de diseño **con datos**: cómo trocear los documentos y qué modelo usar. Medirás calidad, latencia y coste en 3 configuraciones y elegirás una justificándola. Es la pregunta estrella de las entrevistas de AI Engineer: "¿por qué elegiste eso?".

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 26 | 1 h | Técnico | Troceado por frases y configuración por variables de entorno |
| Miércoles 27 | 1 h | Algoritmos | Reverse Linked List y Merge Two Sorted Lists |
| Jueves 28 | 1 h | Técnico | Latencia, tokens y coste en el eval + runs A y B |
| Sábado 30 | 1,5 h | Técnico + carrera | Run C con otro modelo y decisión (30 min) + 2 candidaturas (1 h) |
| Domingo 31 | 15 min | Cierre | Log, checkpoint de enero y PR |

---

### 📖 Qué vas a aprender

**Diseño experimental básico.** Cambias **una sola cosa** cada vez y mantienes fijo todo lo demás: el mismo golden set, el mismo juez y la misma `k`. Si cambias el troceado y el modelo a la vez y mejora, no sabrás por qué.

**Las 3 configuraciones:**

| Run | Troceado | Modelo de DocuChat |
|---|---|---|
| A | Por caracteres (1.000 / 150), el actual | El actual |
| B | **Por frases** (sin cortar frases, solape de 1 frase) | El actual |
| C | El mejor de A y B | **Otro modelo**: uno más barato de Gemini o uno local con Ollama |

**Calidad, latencia y coste, siempre juntos.** Un modelo un 3 % mejor pero 4 veces más caro y lento puede ser la peor decisión. En las empresas se elige con los tres números delante.

**Percentiles.** La latencia media engaña. Se usa la **p50** (mediana: lo que tarda una pregunta normal) y la **p95** (lo que tarda en los peores casos, que es lo que el usuario recuerda).

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana14-experimentos
cd projects/02-docuchat && docker compose up -d
```

---

### Martes 26 · 1 h · Troceado por frases y configuración

**Paso 1 · Configuración (10 min).** En `app/config.py`, pon arriba `from typing import Literal` y añade dentro de la clase `Settings`:

~~~python
    chunk_strategy: Literal["caracteres", "frases"] = "caracteres"
    chat_base_url: str | None = None  # para usar otro proveedor (por ejemplo, Ollama)
    chat_api_key: str | None = None
~~~

Cualquier campo se puede cambiar con una variable de entorno al ejecutar, sin tocar código: `CHUNK_STRATEGY=frases uv run ...`.

**Paso 2 · La función: la escribes tú (30 min).** En `app/ingest.py`:

~~~python
def trocear_por_frases(texto: str, tamano: int, solape_frases: int = 1) -> list[str]:
    # TODO:
    # 1. Divide en frases: re.split(r"(?<=[.!?])\s+", texto.strip())
    # 2. Ve juntando frases mientras el fragmento no pase de `tamano`.
    # 3. Al cerrar un fragmento, el siguiente empieza con sus últimas `solape_frases` frases.
    # 4. Si una frase sola ya pasa de `tamano`, trocéala con trocear(frase, tamano, 0).
    raise NotImplementedError
~~~

Sus tests, al final de `tests/test_ingest.py` (pon los dos `import` arriba del archivo, junto a los que ya hay):

~~~python
import re

from app.ingest import trocear_por_frases

TEXTO = " ".join(f"Esta es la frase número {i}." for i in range(60))


def test_frases_no_supera_tamano():
    assert all(len(f) <= 120 for f in trocear_por_frases(TEXTO, 120))


def test_frases_no_corta_frases():
    assert all(f.endswith(".") for f in trocear_por_frases(TEXTO, 120))


def test_frases_solapa_una_frase():
    fragmentos = trocear_por_frases(TEXTO, 120)
    for a, b in zip(fragmentos, fragmentos[1:]):
        ultima = re.split(r"(?<=[.!?])\s+", a)[-1]
        assert b.startswith(ultima)
~~~

<details>
<summary>Solución</summary>

~~~python
def trocear_por_frases(texto: str, tamano: int, solape_frases: int = 1) -> list[str]:
    frases = [f for f in re.split(r"(?<=[.!?])\s+", texto.strip()) if f]
    fragmentos: list[str] = []
    actual: list[str] = []
    for frase in frases:
        if len(frase) > tamano:  # frase gigante: se trocea por caracteres
            if actual:
                fragmentos.append(" ".join(actual))
                actual = []
            fragmentos.extend(trocear(frase, tamano, 0))
            continue
        if actual and len(" ".join(actual + [frase])) > tamano:
            fragmentos.append(" ".join(actual))
            actual = actual[-solape_frases:] if solape_frases else []
            if len(" ".join(actual + [frase])) > tamano:
                actual = []
        actual.append(frase)
    if actual:
        fragmentos.append(" ".join(actual))
    return fragmentos
~~~
</details>

**Paso 3 · Elegir la estrategia (5 min).** En `app/ingest.py`, añade esta función y úsala en `ingestar_pdf` en lugar de llamar a `trocear` directamente:

~~~python
def partir(texto: str) -> list[str]:
    """Trocea según la estrategia configurada."""
    if settings.chunk_strategy == "frases":
        return trocear_por_frases(texto, settings.chunk_size)
    return trocear(texto, settings.chunk_size, settings.chunk_overlap)
~~~

~~~python
    # dentro de ingestar_pdf
    trozos = [(numero, fragmento) for numero, texto in paginas for fragmento in partir(texto)]
~~~

**Paso 4 · Ingestar una carpeta entera (15 min).** Para el experimento necesitas cargar los mismos PDFs en dos bases de datos. Crea `scripts/ingestar_carpeta.py`:

~~~python
"""Ingesta todos los PDFs de docs/pdfs en la base de datos configurada."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.ingest import ingestar_pdf  # noqa: E402

init_db()
with SessionLocal() as session:
    for pdf in sorted(Path("docs/pdfs").glob("*.pdf")):
        doc = ingestar_pdf(session, pdf.name, pdf.read_bytes())
        print(f"{pdf.name}: {len(doc.chunks)} chunks ({settings.chunk_strategy})")
~~~

```bash
uv run pytest -v
git add -A && git commit -m "DocuChat: troceado por frases y estrategia configurable"
```

---

### Miércoles 27 · 1 h · Algoritmos (Linked List)

En Python, una lista enlazada se representa así (ponlo al principio de cada archivo):

~~~python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


def desde_lista(valores):  # [1, 2, 3] → 1 → 2 → 3
    cabeza = None
    for v in reversed(valores):
        cabeza = ListNode(v, cabeza)
    return cabeza


def a_lista(nodo):  # 1 → 2 → 3 → [1, 2, 3]
    salida = []
    while nodo:
        salida.append(nodo.val)
        nodo = nodo.next
    return salida
~~~

**Reverse Linked List** (Easy) → `practice/algoritmos/reverse_linked_list.py`

~~~python
def reverse_list(head):
    ...


if __name__ == "__main__":
    assert a_lista(reverse_list(desde_lista([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert a_lista(reverse_list(None)) == []
    print("OK")
~~~

**Merge Two Sorted Lists** (Easy) → `practice/algoritmos/merge_two_lists.py`

~~~python
def merge_two_lists(l1, l2):
    ...


if __name__ == "__main__":
    assert a_lista(merge_two_lists(desde_lista([1, 2, 4]), desde_lista([1, 3, 4]))) == [1, 1, 2, 3, 4, 4]
    print("OK")
~~~

<details>
<summary>Pistas</summary>
Reverse: tres variables (anterior, actual, siguiente) y vas dando la vuelta a cada flecha. Merge: un nodo "falso" al principio (dummy) simplifica muchísimo el código.
</details>

---

### Jueves 28 · 1 h · Métricas de rendimiento y runs A y B

**Paso 1 · Medir latencia y tokens (15 min).** En `app/generate.py`, pon arriba `import time` y, dentro de `responder`, mide desde el principio hasta tener la respuesta:

~~~python
    inicio = time.perf_counter()
    # ... búsqueda y llamada al modelo, como ya tenías ...
    latencia = round(time.perf_counter() - inicio, 2)
~~~

Y añade al diccionario que devuelve:

~~~python
        "latency_s": latencia,
        "usage": {"input": respuesta.usage.prompt_tokens, "output": respuesta.usage.completion_tokens},
~~~

En `app/llm.py`, crea un segundo cliente para el chat, para poder cambiar de proveedor (los embeddings siguen siendo de Gemini):

~~~python
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

chat_client = OpenAI(
    base_url=settings.chat_base_url or GEMINI_URL,
    api_key=settings.chat_api_key or settings.google_api_key,
)
~~~

En `app/generate.py`, usa `chat_client` en vez de `client` para la respuesta.

**Paso 2 · Resumen del eval (15 min).** En `evals/run_eval.py`, guarda `latency_s` y `usage` en cada fila. Arriba del archivo:

~~~python
import statistics

from app.config import settings

# Precio por millón de tokens del modelo que estés probando (míralo en su página de precios)
PRECIO_ENTRADA = 0.10
PRECIO_SALIDA = 0.40
~~~

Y dentro de `main`, después de calcular `resumen`:

~~~python
    latencias = [f["latency_s"] for f in filas]
    resumen["config"] = {"chunking": settings.chunk_strategy, "modelo": settings.chat_model}
    resumen["latencia_p50_s"] = statistics.median(latencias)
    resumen["latencia_p95_s"] = statistics.quantiles(latencias, n=20)[18]
    resumen["coste_por_pregunta_usd"] = round(
        sum(f["usage"]["input"] * PRECIO_ENTRADA + f["usage"]["output"] * PRECIO_SALIDA for f in filas)
        / 1_000_000 / len(filas), 6
    )
~~~

Las cifras de precio son de ejemplo: pon las reales de tu modelo.

**Paso 3 · Run A (10 min):**

```bash
uv run python evals/run_eval.py
```

**Paso 4 · Run B, con otra base de datos (20 min).** Así no pisas la de A:

```bash
docker compose exec db psql -U docuchat -c "CREATE DATABASE docuchat_frases"
export DATABASE_URL=postgresql+psycopg://docuchat:docuchat@localhost:5433/docuchat_frases
export CHUNK_STRATEGY=frases
uv run python scripts/ingestar_carpeta.py
uv run python evals/run_eval.py
unset DATABASE_URL CHUNK_STRATEGY
```

```bash
git add -A && git commit -m "Evals: latencia, tokens y coste; runs A y B"
```

---

### Sábado 30 · 1,5 h

**Técnico, 30 min · Run C y la decisión.**

1. Con el troceado que haya ganado entre A y B (si fue B, vuelve a hacer `export` de las dos variables), prueba otro modelo:

    ```bash
    CHAT_MODEL=gemini-flash-lite-latest uv run python evals/run_eval.py
    ```

    **Opcional, con Ollama** (modelos locales; en un Mac Intel funciona, pero lento):

    ```bash
    brew install ollama && ollama serve   # en otra terminal
    ollama pull llama3.2:3b               # o el modelo pequeño que recomiende su web
    CHAT_BASE_URL=http://localhost:11434/v1 CHAT_API_KEY=ollama CHAT_MODEL=llama3.2:3b \
      uv run python evals/run_eval.py
    ```

2. Copia esta tabla en el README de DocuChat (sección **Experiments**) y rellénala con tus 3 runs:

    ```markdown
    | Run | Chunking | Model | hit@5 | Correctness (1-3) | Faithfulness | Abstains on traps | p50 (s) | p95 (s) | Cost/question |
    |---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
    | A | chars 1000/150 | ... | | | | | | | |
    | B | sentences | ... | | | | | | | |
    | C | ... | ... | | | | | | | |

    **Decision:** (2 sentences: what you keep and why, using the numbers)
    ```

3. Deja en `config.py` como valores por defecto los de la configuración ganadora.

**Carrera, 1 h · 2 candidaturas de la ola 2** (30 min cada una, con el método de siempre).

---

### Domingo 31 · 15 min · Cierre y checkpoint de enero

1. **Checkpoint:** compara con la tabla del roadmap (fin de S14: evals, Langfuse y experimento; 20 problemas, 7 candidaturas y 4 contactos). Si vas por detrás en dos de las tres cifras, apúntalo en el log y recorta el técnico de febrero.
2. Log semanal.
3. En Claude Code:
    ```
    Cerramos la semana 14. Revisa el checklist de resources/semanas/semana-14.md,
    ejecuta los tests de DocuChat y dime qué falta. Luego commit, push de
    semana14-experimentos, PR, mergea y deja main al día.
    ```

---

✅ **Checklist**
- [ ] `trocear_por_frases` con sus 3 tests
- [ ] El eval mide latencia p50/p95, tokens y coste
- [ ] 3 runs comparables (mismo golden set y mismo juez)
- [ ] Tabla en el README y decisión justificada en 2 frases
- [ ] 2 problemas de listas enlazadas
- [ ] 2 candidaturas

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `database "docuchat_frases" does not exist` | Falta el `CREATE DATABASE` del paso 4. |
| El run B da los mismos números que el A | La variable `DATABASE_URL` no se aplicó: comprueba con `echo $DATABASE_URL` en la misma terminal. |
| `statistics.StatisticsError` en los cuantiles | Necesitas al menos 2 preguntas: revisa que el golden set se lee entero. |
| Ollama tarda más de un minuto por respuesta | Normal en CPU. Limita el eval a 10 preguntas para este run y dilo en la tabla. |
