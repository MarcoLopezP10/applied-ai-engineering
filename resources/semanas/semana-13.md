# Semana 13 · 18–24 ene · Observabilidad con Langfuse

[← Semana 12](semana-12.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 14 →](semana-14.md)

🎯 **Objetivo:** ver por dentro cada pregunta que recibe DocuChat (qué recuperó, qué prompt mandó, cuánto tardó cada paso y cuánto costó) y tener tu golden set como dataset para comparar versiones.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 19 | 1 h | Técnico | Cuenta de Langfuse y trazas |
| Miércoles 20 | 1 h | Algoritmos | Koko Eating Bananas y Find Minimum in Rotated Sorted Array |
| Jueves 21 | 1 h | Técnico | Golden set como dataset y primera ejecución |
| Sábado 23 | 1,5 h | Técnico + carrera | Leer las trazas (30 min) + entrevista simulada y 1 candidatura (1 h) |
| Domingo 24 | 15 min | Cierre | Log y PR |

Material de apoyo: roadmap técnico, semana 22, y la [documentación de Langfuse](https://langfuse.com/docs).

---

### 📖 Qué vas a aprender

**Observabilidad.** En producción no puedes poner `print`. Cuando un usuario dice "me ha respondido mal", necesitas ver exactamente qué pasó en esa pregunta. Una **traza** es el registro de una petición completa, y dentro tiene **pasos** (*spans*): embedding, búsqueda y llamada al LLM, cada uno con su entrada, su salida, su duración y sus tokens.

**Por qué Langfuse.** Es open source, tiene una capa gratuita en la nube y aparece en las ofertas de AI Engineer junto a LangSmith. Lo que aprendas aquí sirve para cualquiera de las dos.

**Datasets y experimentos.** Tu golden set vive dentro de Langfuse. Cada vez que ejecutas el eval sobre él, se guarda como un *run* con nombre ("v1-base", "v2-chunking-frases"…) y puedes comparar runs uno al lado del otro.

> Langfuse cambia rápido. El código de esta guía es para la versión 3 del SDK de Python. Si algo no coincide, busca en su documentación "Python SDK" y "Datasets".

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana13-langfuse
cd projects/02-docuchat && docker compose up -d
uv add langfuse
```

---

### Martes 19 · 1 h · Trazas

**Paso 1 · Cuenta (10 min).** Regístrate en [cloud.langfuse.com](https://cloud.langfuse.com) (región UE), crea un proyecto "docuchat" y genera unas API keys. Añádelas al `.env` de la raíz del repo:

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

**Paso 2 · Trazar las llamadas al modelo (10 min).** En `app/llm.py`, cambia **una sola línea**:

~~~python
from langfuse.openai import OpenAI  # antes: from openai import OpenAI
~~~

Es un sustituto directo: registra cada llamada (prompt, respuesta, tokens y latencia) sin cambiar nada más.

Como `pydantic-settings` no carga en el entorno las variables que no conoce, añade al principio de `app/config.py`:

~~~python
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))  # para que Langfuse lea sus claves del .env
~~~

**Paso 3 · Agrupar los pasos en una traza (25 min).** Decora las funciones con `@observe()`:

~~~python
# app/retrieval.py
from langfuse import observe

@observe()
def buscar(session, pregunta, k=5):
    ...
~~~

~~~python
# app/generate.py
from langfuse import observe

@observe()
def responder(session, pregunta, k=5):
    ...
~~~

Haz lo mismo con `embed` en `app/llm.py`. Así cada `/ask` queda como una traza con 3 pasos dentro: `responder` → `buscar` → `embed`, más la llamada al LLM.

**Paso 4 · Que no se pierdan trazas al parar la API (5 min).** En `app/main.py`:

~~~python
from langfuse import get_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    get_client().flush()  # envía las trazas pendientes antes de cerrar
~~~

**Paso 5 · Comprobar (10 min).** Arranca la API, haz 3 preguntas desde `/docs` y abre Langfuse → **Tracing**.

**Está bien si** ves 3 trazas y, al abrir una, el árbol `responder` → `buscar` → `embed` → llamada al modelo, con el prompt completo (incluidos los 5 fragmentos) y la respuesta.

```bash
git add -A && git commit -m "DocuChat: trazas con Langfuse"
```

---

### Miércoles 20 · 1 h · Algoritmos (Binary Search sobre la respuesta)

**Koko Eating Bananas** (Medium) → `practice/algoritmos/koko_bananas.py`

~~~python
def min_eating_speed(piles: list[int], h: int) -> int:
    ...


if __name__ == "__main__":
    assert min_eating_speed([3, 6, 7, 11], 8) == 4
    assert min_eating_speed([30, 11, 23, 4, 20], 5) == 30
    print("OK")
~~~

<details>
<summary>Pista</summary>
No buscas en la lista: buscas la velocidad. Entre 1 y max(piles), haz búsqueda binaria preguntando "¿a esta velocidad termina en h horas?".
</details>

**Find Minimum in Rotated Sorted Array** (Medium) → `practice/algoritmos/find_min_rotated.py`

~~~python
def find_min(nums: list[int]) -> int:
    ...


if __name__ == "__main__":
    assert find_min([3, 4, 5, 1, 2]) == 1
    assert find_min([4, 5, 6, 7, 0, 1, 2]) == 0
    assert find_min([11, 13, 15, 17]) == 11
    print("OK")
~~~

<details>
<summary>Pista</summary>
Compara el elemento del medio con el de la derecha: te dice en qué mitad está el "salto".
</details>

---

### Jueves 21 · 1 h · Golden set como dataset

**Paso 1 · Subirlo (20 min).** Crea `evals/subir_dataset.py`:

~~~python
"""Sube el golden set a Langfuse como dataset (solo hace falta una vez)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app.config  # noqa: E402,F401  (carga el .env)
from langfuse import get_client  # noqa: E402

NOMBRE = "docuchat-golden"
langfuse = get_client()
langfuse.create_dataset(name=NOMBRE, description="30 preguntas sobre apuntes del máster (5 trampa)")

for linea in (Path(__file__).parent / "golden_set.jsonl").read_text(encoding="utf-8").splitlines():
    if not linea.strip():
        continue
    caso = json.loads(linea)
    langfuse.create_dataset_item(
        dataset_name=NOMBRE,
        input={"question": caso["question"]},
        expected_output={"answer": caso["expected_answer"], "document": caso["document"], "page": caso["page"]},
        metadata={"id": caso["id"]},
    )
langfuse.flush()
print("Dataset subido")
~~~

Ejecútalo con `uv run python evals/subir_dataset.py` y comprueba en Langfuse → **Datasets** que hay 30 items.

**Paso 2 · Ejecutar un run (40 min).** Crea `evals/run_langfuse.py`. Recorre el dataset, ejecuta DocuChat en cada item enlazando la traza al run y registra la nota del juez como *score*:

~~~python
"""Ejecuta DocuChat sobre el dataset de Langfuse y guarda el run con un nombre."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langfuse import get_client  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.generate import responder  # noqa: E402
from evals.juez import corregir  # noqa: E402

NOMBRE_RUN = sys.argv[1] if len(sys.argv) > 1 else "v1-base"

langfuse = get_client()
dataset = langfuse.get_dataset("docuchat-golden")

with SessionLocal() as session:
    for item in dataset.items:
        with item.run(run_name=NOMBRE_RUN) as span:  # enlaza esta traza con el item y el run
            r = responder(session, item.input["question"])
            span.update_trace(input=item.input, output=r["answer"])
            esperada = item.expected_output["answer"]
            if esperada:  # las trampas no se puntúan con el juez
                nota = corregir(item.input["question"], esperada, r["answer"]).score
                span.score_trace(name="correccion", value=nota)
        print("·", end="", flush=True)

langfuse.flush()
print(f"\nRun '{NOMBRE_RUN}' terminado")
~~~

```bash
uv run python evals/run_langfuse.py v1-base
```

**Está bien si** en Langfuse → Datasets → docuchat-golden → **Runs** aparece "v1-base" con 30 trazas y la media del score "correccion".

> Si `item.run` no existe en tu versión del SDK, busca en la documentación de Langfuse "dataset runs" o "experiments" con el SDK de Python. La idea es la misma: ejecutar cada item y enlazar su traza con el nombre del run.

```bash
git add -A && git commit -m "Evals: golden set como dataset de Langfuse y run v1-base"
```

---

### Sábado 23 · 1,5 h

**Técnico, 30 min · Leer las trazas.** En Langfuse:

1. Ordena las trazas por **latencia**. ¿Qué paso es el más lento: embedding, búsqueda o LLM?
2. Mira los **tokens** de entrada de una pregunta. ¿Cuánto ocupa el prompt con 5 fragmentos?
3. **Coste:** si Langfuse no muestra coste para tu modelo de Gemini, añádelo en Settings → Models con el precio por millón de tokens de la página de precios de Gemini.

Apunta en `docs/notas.md`: **latencia media por pregunta, paso más lento, tokens medios y coste por pregunta.** Son las tres cifras que te preguntarán en cualquier entrevista de AI Engineer sobre este proyecto.

**Carrera, 1 h:**

1. **Entrevista simulada (10 min para reservarla).** Pide cita en IE Careers para una entrevista simulada técnica o de comportamiento en las próximas 2 semanas. Cuando la hagas, cuenta como bloque de carrera de esa semana.
2. **1 candidatura de la ola 2 (50 min)** con el método de siempre.

---

### Domingo 24 · 15 min · Cierre

1. README de DocuChat: añade una sección **Observability** con 2 líneas y una captura de una traza (`docs/traza.png`).
2. Log semanal con las horas reales de esta segunda semana. Si la media de las dos es inferior a 4 h, recorta el técnico de las próximas semanas.
3. En Claude Code:
    ```
    Cerramos la semana 13. Revisa el checklist de resources/semanas/semana-13.md
    y dime qué falta. Luego commit, push de semana13-langfuse, PR, mergea y deja main al día.
    ```

---

✅ **Checklist**
- [ ] Cada `/ask` deja una traza con sus pasos
- [ ] Golden set subido como dataset
- [ ] Run "v1-base" con score de corrección
- [ ] Sé decir latencia media, paso más lento, tokens y coste por pregunta
- [ ] Entrevista simulada reservada y 1 candidatura
- [ ] 2 problemas de algoritmos

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| No aparece ninguna traza | Faltan las claves en el entorno: comprueba el `load_dotenv` de `config.py` y que `LANGFUSE_HOST` sea el de la región donde creaste el proyecto. |
| Las trazas aparecen sueltas, no en árbol | Falta `@observe()` en `responder`, que es la función de más arriba. |
| Las trazas del eval no llegan | En los scripts hay que llamar a `get_client().flush()` al final. |
| `ModuleNotFoundError: evals` | Crea `evals/__init__.py`. |
