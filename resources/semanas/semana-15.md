# Semana 15 · 1–7 feb · Búsqueda híbrida

[← Semana 14](semana-14.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 16 →](semana-16.md)

🎯 **Objetivo:** mejorar la recuperación combinando la búsqueda por significado (vectores) con la búsqueda por palabras exactas (texto completo de Postgres), y **demostrar con el eval** si mejora o no.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 2 | 1 h | Técnico | Búsqueda de texto completo en Postgres |
| Miércoles 3 | 1 h | Algoritmos | Linked List Cycle y Reorder List |
| Jueves 4 | 1 h | Técnico | Fusión de resultados (RRF), la escribes tú |
| Sábado 6 | 1,5 h | Técnico + carrera | Eval vector frente a híbrida (30 min) + 1 candidatura y 1 mensaje (1 h) |
| Domingo 7 | 15 min | Cierre | Log y PR |

Material de apoyo: roadmap técnico, semanas 19–20.

---

### 📖 Qué vas a aprender

**Cada búsqueda falla en cosas distintas:**

| Búsqueda | Buena en | Mala en |
|---|---|---|
| Vectorial (significado) | Sinónimos y preguntas con otras palabras | Siglas, códigos, nombres propios y números exactos ("ISO 27001", "tabla 3.2") |
| Texto completo (palabras) | Términos exactos y siglas | Sinónimos y paráfrasis |

**Búsqueda híbrida.** Lanzas las dos, cada una devuelve sus 20 mejores, y las **fusionas**.

**Reciprocal Rank Fusion (RRF).** La forma más sencilla y robusta de fusionar. Cada documento suma `1 / (60 + posición)` por cada lista en la que aparece. Si sale arriba en las dos, gana. No necesita que las puntuaciones de cada búsqueda estén en la misma escala, que es justo el problema de mezclarlas.

**Full-text search de Postgres.** Convierte el texto en un `tsvector` (palabras normalizadas: "running" → "run") y la pregunta en un `tsquery`. Con un índice GIN es muy rápido y no necesitas otra herramienta como Elasticsearch.

**La alternativa: reranking.** Recuperas 20 y un modelo especializado los reordena leyendo pregunta y fragmento juntos. Suele mejorar más, pero añade coste y latencia. Si te sobra tiempo, pruébalo como run extra.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana15-busqueda-hibrida
cd projects/02-docuchat && docker compose up -d
```

---

### Martes 2 · 1 h · Texto completo en Postgres

**Paso 1 · Configuración (5 min).** En `app/config.py`, dentro de `Settings`:

~~~python
    search_mode: Literal["vector", "hybrid"] = "vector"
    fulltext_language: str = "english"  # el idioma de tus PDFs: "english" o "spanish"
~~~

**Paso 2 · Columna e índice (20 min).** En `app/db.py`, añade al final de `init_db()`. Así se crea también en bases de datos nuevas:

~~~python
    with engine.begin() as conn:  # una sentencia por execute
        conn.execute(text(
            "ALTER TABLE chunks ADD COLUMN IF NOT EXISTS tsv tsvector "
            f"GENERATED ALWAYS AS (to_tsvector('{settings.fulltext_language}', text)) STORED"
        ))
        conn.execute(text("CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING gin (tsv)"))
~~~

`GENERATED ALWAYS ... STORED` hace que Postgres calcule y actualice la columna solo; tú no tienes que tocar la ingesta.

Arranca la API una vez (`uv run uvicorn app.main:app`) para que `init_db` aplique el cambio y párala.

**Paso 3 · Probarlo a mano (15 min):**

```bash
docker compose exec db psql -U docuchat -d docuchat
```

```sql
SELECT page, ts_rank_cd(tsv, q) AS rank, left(text, 80)
FROM chunks, websearch_to_tsquery('english', 'normal form database') AS q
WHERE tsv @@ q
ORDER BY rank DESC
LIMIT 5;
```

Cambia la búsqueda por un término exacto de tus apuntes (una sigla o un nombre). **Está bien si** devuelve fragmentos que contienen esas palabras.

**Paso 4 · Las dos búsquedas por separado (20 min).** En `app/retrieval.py`, añade:

~~~python
from sqlalchemy import text

from app.config import settings

CANDIDATOS = 20  # cuántos trae cada búsqueda antes de fusionar


def ids_vectorial(session: Session, vector: list[float], n: int = CANDIDATOS) -> list[int]:
    distancia = Chunk.embedding.cosine_distance(vector)
    return list(session.scalars(select(Chunk.id).order_by(distancia).limit(n)))


def ids_texto(session: Session, pregunta: str, n: int = CANDIDATOS) -> list[int]:
    idioma = settings.fulltext_language
    consulta = text(f"""
        SELECT id FROM chunks
        WHERE tsv @@ websearch_to_tsquery('{idioma}', :q)
        ORDER BY ts_rank_cd(tsv, websearch_to_tsquery('{idioma}', :q)) DESC
        LIMIT :n
    """)
    return list(session.scalars(consulta, {"q": pregunta, "n": n}))
~~~

Fíjate en que la pregunta va como parámetro (`:q`) y nunca pegada en el SQL: así se evita la inyección SQL. El idioma sí va pegado, porque viene de tu configuración y no del usuario.

```bash
git add -A && git commit -m "DocuChat: búsqueda de texto completo en Postgres"
```

---

### Miércoles 3 · 1 h · Algoritmos

Usa `ListNode`, `desde_lista` y `a_lista` de la semana 14.

**Linked List Cycle** (Easy) → `practice/algoritmos/linked_list_cycle.py`

~~~python
def has_cycle(head) -> bool:
    ...


if __name__ == "__main__":
    a = desde_lista([3, 2, 0, -4])
    a.next.next.next.next = a.next  # el último apunta al segundo: hay ciclo
    assert has_cycle(a) is True
    assert has_cycle(desde_lista([1, 2])) is False
    print("OK")
~~~

<details>
<summary>Pista</summary>
Dos punteros: uno avanza de 1 en 1 y otro de 2 en 2. Si hay ciclo, acaban encontrándose (algoritmo de Floyd, "liebre y tortuga").
</details>

**Reorder List** (Medium) → `practice/algoritmos/reorder_list.py`

~~~python
def reorder_list(head) -> None:
    """Modifica la lista: L0 → Ln → L1 → Ln-1 → L2 → ..."""
    ...


if __name__ == "__main__":
    lista = desde_lista([1, 2, 3, 4, 5])
    reorder_list(lista)
    assert a_lista(lista) == [1, 5, 2, 4, 3]
    print("OK")
~~~

<details>
<summary>Pista</summary>
Tres pasos que ya sabes hacer: encontrar la mitad (liebre y tortuga), darle la vuelta a la segunda mitad (semana 14) e intercalar las dos mitades.
</details>

---

### Jueves 4 · 1 h · La fusión (RRF)

**Paso 1 · La escribes tú (20 min).** En `app/retrieval.py`:

~~~python
from collections import defaultdict


def rrf(listas: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    # TODO: cada id suma 1 / (k + posición) por cada lista en la que aparece
    #       (la posición empieza en 1). Devuelve [(id, puntuación), ...]
    #       ordenado de mayor a menor puntuación.
    raise NotImplementedError
~~~

Antes, sus tests en `tests/test_retrieval.py`:

~~~python
import os

os.environ.setdefault("GOOGLE_API_KEY", "clave-de-test")

from app.retrieval import rrf  # noqa: E402


def test_gana_el_que_esta_en_las_dos_listas():
    resultado = rrf([[1, 2, 3], [9, 3, 8]])
    assert resultado[0][0] == 3


def test_respeta_el_orden_dentro_de_una_lista():
    ids = [i for i, _ in rrf([[5, 6, 7]])]
    assert ids == [5, 6, 7]


def test_puntuacion_exacta():
    [(id_, puntuacion)] = rrf([[42]], k=60)
    assert id_ == 42 and abs(puntuacion - 1 / 61) < 1e-9
~~~

<details>
<summary>Solución</summary>

~~~python
def rrf(listas: list[list[int]], k: int = 60) -> list[tuple[int, float]]:
    puntuaciones: dict[int, float] = defaultdict(float)
    for lista in listas:
        for posicion, id_ in enumerate(lista, start=1):
            puntuaciones[id_] += 1 / (k + posicion)
    return sorted(puntuaciones.items(), key=lambda par: par[1], reverse=True)
~~~
</details>

**Paso 2 · Conectarlo en `buscar` (30 min).** Sustituye tu `buscar` por esta versión, que soporta los dos modos:

~~~python
def cargar(session: Session, puntuados: list[tuple[int, float]]) -> list[dict]:
    """Trae los chunks de la BD respetando el orden de la fusión."""
    ids = [i for i, _ in puntuados]
    chunks = {c.id: c for c in session.scalars(select(Chunk).where(Chunk.id.in_(ids)))}
    return [
        {"document": chunks[i].document.filename, "page": chunks[i].page,
         "text": chunks[i].text, "score": round(p, 4)}
        for i, p in puntuados
    ]


@observe()
def buscar(session: Session, pregunta: str, k: int = 5) -> list[dict]:
    vector = embed([pregunta])[0]
    if settings.search_mode == "hybrid":
        fusion = rrf([ids_vectorial(session, vector), ids_texto(session, pregunta)])
        return cargar(session, fusion[:k])
    distancia = Chunk.embedding.cosine_distance(vector).label("distancia")
    filas = session.execute(
        select(Chunk, Document.filename, distancia).join(Document).order_by(distancia).limit(k)
    ).all()
    return [
        {"document": nombre, "page": c.page, "text": c.text, "score": round(1 - d, 3)}
        for c, nombre, d in filas
    ]
~~~

```bash
uv run pytest -v
git add -A && git commit -m "DocuChat: búsqueda híbrida con Reciprocal Rank Fusion"
```

---

### Sábado 6 · 1,5 h

**Técnico, 30 min · ¿Mejora?** Con la configuración ganadora de la semana 14:

```bash
uv run python evals/run_eval.py                      # vector (referencia)
SEARCH_MODE=hybrid uv run python evals/run_eval.py   # híbrida
```

Compara los dos JSON y:

1. Añade una fila "D · hybrid" a la tabla **Experiments** del README.
2. Busca las preguntas que **cambiaron** de fallo a acierto (o al revés) y apunta de qué tipo son. Lo normal es que la híbrida gane en siglas y términos exactos.
3. **Decide:** si mejora el hit@5 sin empeorar lo demás, pon `search_mode = "hybrid"` por defecto. Si no mejora, déjalo en `"vector"` y escríbelo así en el README: "Hybrid search did not improve hit@5 on my dataset (X vs Y), so I kept vector search". Descartar una mejora con datos demuestra criterio.

**Carrera, 1 h:**

1. **1 candidatura de la ola 3** (40 min). Empiezan las scale-ups y startups de IA. Aquí tu portfolio pesa más que la marca: en la carta o en el formulario, enlaza DocuChat y pon tu número de hit@5.
2. **1 mensaje** (20 min) a alguien de una empresa de la ola 3.

---

### Domingo 7 · 15 min · Cierre

1. Log semanal.
2. En Claude Code:
    ```
    Cerramos la semana 15. Revisa el checklist de resources/semanas/semana-15.md,
    ejecuta los tests y dime qué falta. Luego commit, push de semana15-busqueda-hibrida,
    PR, mergea y deja main al día.
    ```

---

✅ **Checklist**
- [ ] Columna `tsv` con índice GIN creada desde `init_db`
- [ ] `rrf` con sus 3 tests
- [ ] Búsqueda híbrida activable con `SEARCH_MODE`
- [ ] Run D en la tabla y decisión escrita, mejore o no
- [ ] 2 problemas de listas enlazadas
- [ ] 1 candidatura de la ola 3 y 1 mensaje

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `column "tsv" does not exist` | `init_db()` no se ha ejecutado tras el cambio: arranca la API una vez. |
| La búsqueda de texto no devuelve nada | Revisa `fulltext_language`. Si tus PDFs están en inglés y preguntas en español, no habrá coincidencias: es esperable. |
| `KeyError` en `cargar` | Algún id de la fusión no está en la BD. Pasa si ejecutas contra otra base de datos distinta de la que usaste para ingestar. |
| La híbrida empeora | Prueba a bajar `CANDIDATOS` a 10, o a dar más peso al vector repitiendo su lista dos veces en `rrf`. Documenta lo que pruebes. |
