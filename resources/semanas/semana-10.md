# Semana 10 · 28 dic – 3 ene · DocuChat v0: ingesta y búsqueda

[← Semana 9](semana-09.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 11 →](semana-11.md)

🎯 **Objetivo:** primera versión de tu proyecto estrella. Subes un PDF a una API, se trocea, se convierte en embeddings y se guarda en pgvector; luego buscas por significado y te devuelve los fragmentos con su página.

**Navidad: unas 10 h.** Libres el 31 y el 1.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Lunes 28 | 2,5 h | Técnico | Proyecto, base de datos y modelos con SQLAlchemy |
| Martes 29 | 2,5 h | Técnico | Ingesta: PDF → fragmentos → embeddings |
| Miércoles 30 | 2 h + 1 h | Técnico + algoritmos | Búsqueda, endpoint e índice HNSW + Best Time to Buy and Sell Stock |
| Sábado 2 | 2 h | Algoritmos + carrera | Longest Substring + 4 historias STAR y CV |
| Domingo 3 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**RAG (Retrieval-Augmented Generation).** Un LLM no conoce tus apuntes. RAG consiste en buscar los trozos relevantes de tus documentos y dárselos al modelo junto con la pregunta. Tiene dos fases:

```
INGESTA (una vez por documento)              PREGUNTA (cada vez)
PDF → texto por página → fragmentos          pregunta → embedding
    → embeddings → base de datos                 → buscar los 5 fragmentos más cercanos
                                                 → (semana 11) LLM responde con ellos
```

Esta semana haces la ingesta y la búsqueda. La semana que viene, la respuesta.

**Chunking (trocear).** No se guarda el PDF entero como un solo vector: un vector de 50 páginas no representa nada concreto. Se parte en fragmentos de unos 1.000 caracteres. Se dejan **150 de solapamiento** para que una idea que cae en el corte no se pierda.

**SQLAlchemy (ORM).** Defines las tablas como clases de Python y trabajas con objetos en vez de escribir SQL a mano. Es lo que se usa en casi todos los backends de Python.

**Índice HNSW.** Sin índice, Postgres compara la pregunta con **todos** los vectores. HNSW es un grafo que encuentra los más cercanos sin mirarlos todos: un poco menos exacto y muchísimo más rápido cuando hay miles.

Material de apoyo: roadmap técnico, semanas 9–10 (SQL y SQLAlchemy), 13 (pgvector) y 14 (chunking).

---

### Lunes 28 · 2,5 h · Proyecto, base de datos y modelos

**Paso 1 · Crear el proyecto (20 min):**

```bash
git checkout main && git pull
git checkout -b semana10-docuchat-ingesta
mkdir -p projects/02-docuchat && cd projects/02-docuchat
uv init --app --name docuchat .
rm main.py   # uv crea uno de ejemplo; no lo necesitamos
mkdir -p app tests evals docs
touch app/__init__.py
uv add fastapi "uvicorn[standard]" python-multipart sqlalchemy "psycopg[binary]" pgvector pypdf openai python-dotenv pydantic-settings
uv add --dev pytest httpx
```

Añade al final de `pyproject.toml` estas líneas, para que los tests puedan importar el código del proyecto:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

**Paso 2 · Base de datos propia (15 min).** Crea `projects/02-docuchat/docker-compose.yml`. Usa el puerto **5433** para no chocar con el de la semana 9:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: docuchat
      POSTGRES_PASSWORD: docuchat
      POSTGRES_DB: docuchat
    ports:
      - "5433:5432"
    volumes:
      - docuchat_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docuchat -d docuchat"]
      interval: 5s
      retries: 10

volumes:
  docuchat_data:
```

```bash
docker compose up -d
```

**Paso 3 · Configuración (15 min).** Crea `app/config.py`. Toda la configuración está en un único sitio:

~~~python
"""Configuración de DocuChat: un único sitio para todo lo que puede cambiar."""
from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv(usecwd=True), extra="ignore")

    google_api_key: str
    database_url: str = "postgresql+psycopg://docuchat:docuchat@localhost:5433/docuchat"
    chat_model: str = "gemini-3.8-flash"
    embedding_model: str = "gemini-embedding-001"  # comprueba el nombre actual en la doc de Gemini
    embedding_dim: int = 768
    chunk_size: int = 1000
    chunk_overlap: int = 150


settings = Settings()
~~~

**Paso 4 · Tablas con SQLAlchemy (60 min).** Crea `app/db.py`. Léelo despacio: un `Document` tiene muchos `Chunk`, y cada chunk guarda su página, su texto y su vector.

~~~python
"""Base de datos: tablas de documentos y fragmentos con su embedding."""
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    pages: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    page: Mapped[int]
    text: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(settings.embedding_dim))
    document: Mapped[Document] = relationship(back_populates="chunks")


def init_db() -> None:
    """Crea la extensión vector y las tablas si no existen."""
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
~~~

**Paso 5 · Comprobar (20 min):**

```bash
uv run python -c "from app.db import init_db; init_db(); print('tablas creadas')"
docker compose exec db psql -U docuchat -d docuchat -c "\d chunks"
```

**Está bien si** ves la tabla `chunks` con la columna `embedding` de tipo `vector(768)`.

**Paso 6 · Ejercicio de comprensión (20 min).** Responde en `docs/notas.md`:

- ¿Qué pasa con los chunks si borras un documento? Mira `cascade` y `ondelete`.
- ¿Por qué el tamaño del vector está en la configuración y no escrito en `db.py`?

```bash
git add -A && git commit -m "DocuChat: proyecto, configuración y modelos de datos"
```

---

### Martes 29 · 2,5 h · Ingesta

**Paso 1 · Embeddings por lotes (15 min).** Crea `app/llm.py`:

~~~python
"""Acceso a los modelos de Gemini a través del SDK de OpenAI."""
from openai import OpenAI

from app.config import settings

client = OpenAI(
    api_key=settings.google_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

LOTE = 50  # textos por llamada: menos llamadas y menos riesgo de límite de tamaño


def embed(textos: list[str]) -> list[list[float]]:
    vectores: list[list[float]] = []
    for i in range(0, len(textos), LOTE):
        respuesta = client.embeddings.create(
            model=settings.embedding_model,
            input=textos[i : i + LOTE],
            dimensions=settings.embedding_dim,
        )
        vectores.extend(d.embedding for d in respuesta.data)
    return vectores
~~~

**Paso 2 · Trocear: lo escribes tú (45 min).** Crea `app/ingest.py` con este esqueleto:

~~~python
"""Ingesta: PDF → páginas → fragmentos → embeddings → base de datos."""
import io
import re

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Chunk, Document
from app.llm import embed


def extraer_paginas(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Devuelve [(número de página empezando en 1, texto limpio), ...]."""
    lector = PdfReader(io.BytesIO(pdf_bytes))
    paginas = []
    for numero, pagina in enumerate(lector.pages, start=1):
        texto = re.sub(r"\s+", " ", pagina.extract_text() or "").strip()
        if texto:
            paginas.append((numero, texto))
    return paginas


def trocear(texto: str, tamano: int, solape: int) -> list[str]:
    # TODO: lo escribes tú. Reglas:
    #  - Fragmentos de como máximo `tamano` caracteres.
    #  - Cada fragmento empieza `tamano - solape` caracteres después del anterior.
    #  - Si puedes, corta en el último espacio antes del límite para no partir palabras.
    #  - Texto vacío → lista vacía. Texto más corto que `tamano` → un único fragmento.
    raise NotImplementedError
~~~

Antes de programarlo, escribe sus tests en `tests/test_ingest.py`. Así sabes exactamente qué tiene que cumplir:

~~~python
import os

os.environ.setdefault("GOOGLE_API_KEY", "clave-de-test")

from app.ingest import trocear  # noqa: E402


def test_texto_vacio():
    assert trocear("", 100, 20) == []


def test_texto_corto_es_un_solo_fragmento():
    assert trocear("hola mundo", 100, 20) == ["hola mundo"]


def test_ningun_fragmento_supera_el_tamano():
    texto = "palabra " * 500
    assert all(len(f) <= 100 for f in trocear(texto, 100, 20))


def test_hay_solapamiento_entre_fragmentos():
    texto = " ".join(f"p{i}" for i in range(300))
    fragmentos = trocear(texto, 100, 30)
    ultima_palabra = fragmentos[0].split()[-1]
    assert ultima_palabra in fragmentos[1]


def test_no_parte_palabras():
    texto = "abcdefghij " * 50
    for fragmento in trocear(texto, 55, 10):
        assert all(palabra == "abcdefghij" for palabra in fragmento.split())
~~~

```bash
uv run pytest tests/test_ingest.py -v
```

Tienen que fallar (aún no hay función). Ahora escribe `trocear` hasta que pasen los 5.

<details>
<summary>Solución (ábrela solo si llevas 25 min)</summary>

~~~python
def trocear(texto: str, tamano: int, solape: int) -> list[str]:
    texto = texto.strip()
    if not texto:
        return []
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + tamano, len(texto))
        if fin < len(texto):  # no es el último: intenta cortar en un espacio
            espacio = texto.rfind(" ", inicio, fin)
            if espacio > inicio:
                fin = espacio
        fragmentos.append(texto[inicio:fin].strip())
        if fin >= len(texto):
            break
        siguiente = max(fin - solape, inicio + 1)
        # empieza en el principio de una palabra
        while siguiente < fin and texto[siguiente - 1] != " ":
            siguiente += 1
        inicio = siguiente
    return [f for f in fragmentos if f]
~~~
</details>

**Paso 3 · Juntarlo todo (30 min).** Añade a `app/ingest.py`:

~~~python
def ingestar_pdf(session: Session, nombre: str, pdf_bytes: bytes) -> Document:
    paginas = extraer_paginas(pdf_bytes)
    documento = Document(filename=nombre, pages=len(paginas))
    trozos = [
        (numero, fragmento)
        for numero, texto in paginas
        for fragmento in trocear(texto, settings.chunk_size, settings.chunk_overlap)
    ]
    vectores = embed([fragmento for _, fragmento in trozos])
    documento.chunks = [
        Chunk(page=numero, text=fragmento, embedding=vector)
        for (numero, fragmento), vector in zip(trozos, vectores)
    ]
    session.add(documento)
    session.commit()
    session.refresh(documento)
    return documento
~~~

Fíjate en que los fragmentos se hacen **por página**: así cada uno sabe de qué página viene, y esa es la base de las citas.

**Paso 4 · La API (40 min).** Crea `app/main.py`:

~~~python
"""DocuChat API."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import Chunk, Document, SessionLocal, init_db
from app.ingest import ingestar_pdf


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # al arrancar, crea tablas si hace falta
    yield


app = FastAPI(title="DocuChat", lifespan=lifespan)


def get_session():
    with SessionLocal() as session:
        yield session


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/documents")
def subir_documento(file: UploadFile = File(...), session: Session = Depends(get_session)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
    documento = ingestar_pdf(session, file.filename, file.file.read())
    return {"id": documento.id, "filename": documento.filename,
            "pages": documento.pages, "chunks": len(documento.chunks)}


@app.get("/documents")
def listar_documentos(session: Session = Depends(get_session)):
    filas = session.execute(
        select(Document.id, Document.filename, Document.pages, func.count(Chunk.id))
        .join(Chunk, isouter=True)
        .group_by(Document.id)
    ).all()
    return [{"id": i, "filename": f, "pages": p, "chunks": c} for i, f, p, c in filas]
~~~

Arranca y prueba:

```bash
uv run uvicorn app.main:app --reload
```

Abre http://localhost:8000/docs → `POST /documents` → *Try it out* → sube un PDF de clase.

**Está bien si** devuelve el número de páginas y de chunks, y `GET /documents` lo lista. Un PDF de 20 páginas suele dar entre 40 y 80 chunks.

```bash
git add -A && git commit -m "DocuChat: ingesta de PDF con chunking y embeddings"
```

---

### Miércoles 30 · 3 h · Búsqueda, índice y algoritmos

**Paso 1 · La búsqueda: la escribes tú (45 min).** Crea `app/retrieval.py`:

~~~python
"""Búsqueda semántica de fragmentos."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Chunk, Document
from app.llm import embed


def buscar(session: Session, pregunta: str, k: int = 5) -> list[dict]:
    # TODO:
    # 1. vector = embedding de la pregunta (embed([pregunta])[0])
    # 2. distancia = Chunk.embedding.cosine_distance(vector).label("distancia")
    # 3. select(Chunk, Document.filename, distancia).join(Document)
    #       .order_by(distancia).limit(k)
    # 4. Devuelve una lista de diccionarios con:
    #    document, page, text, score (usa 1 - distancia: así 1 es "muy parecido")
    raise NotImplementedError
~~~

<details>
<summary>Solución</summary>

~~~python
def buscar(session: Session, pregunta: str, k: int = 5) -> list[dict]:
    vector = embed([pregunta])[0]
    distancia = Chunk.embedding.cosine_distance(vector).label("distancia")
    filas = session.execute(
        select(Chunk, Document.filename, distancia).join(Document).order_by(distancia).limit(k)
    ).all()
    return [
        {"document": nombre, "page": chunk.page, "text": chunk.text, "score": round(1 - d, 3)}
        for chunk, nombre, d in filas
    ]
~~~
</details>

Añade el endpoint a `app/main.py`:

~~~python
from app.retrieval import buscar


@app.get("/search")
def search(q: str, k: int = 5, session: Session = Depends(get_session)):
    return buscar(session, q, k)
~~~

Sube 2 PDFs más de clase y prueba en `/docs` preguntas reales del temario. **Está bien si** los fragmentos devueltos responden a la pregunta y la página coincide con la del PDF.

**Paso 2 · Índice HNSW (45 min).** Añade a `app/db.py`, debajo de la clase `Chunk`:

~~~python
from sqlalchemy import Index

Index(
    "chunks_embedding_hnsw",
    Chunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"},  # el mismo tipo de distancia que buscas
)
~~~

Como `create_all` no modifica tablas que ya existen, borra y recrea la base de datos: `docker compose down -v && docker compose up -d`. Después vuelve a subir los PDFs.

Comprueba que el índice se usa:

```bash
docker compose exec db psql -U docuchat -d docuchat
```

```sql
SET enable_seqscan = off;  -- con pocos datos Postgres prefiere no usar el índice; lo forzamos para verlo
EXPLAIN ANALYZE
SELECT id FROM chunks ORDER BY embedding <=> (SELECT embedding FROM chunks LIMIT 1) LIMIT 5;
```

**Está bien si** el plan dice `Index Scan using chunks_embedding_hnsw`. Con unos cientos de chunks no notarás la diferencia de velocidad; con decenas de miles, la búsqueda pasa de cientos de milisegundos a unos pocos. Apúntalo en `docs/notas.md`: es una pregunta típica de entrevista.

```bash
git add -A && git commit -m "DocuChat: búsqueda semántica con índice HNSW"
```

**Paso 3 · Algoritmos (1 h). Best Time to Buy and Sell Stock** (Easy, patrón Sliding Window) → `practice/algoritmos/best_time_stock.py`

~~~python
def max_profit(prices: list[int]) -> int:
    ...


if __name__ == "__main__":
    assert max_profit([7, 1, 5, 3, 6, 4]) == 5
    assert max_profit([7, 6, 4, 3, 1]) == 0
    print("OK")
~~~

<details>
<summary>Pista</summary>
Recorre los precios guardando el mínimo visto hasta ahora. En cada día, la ganancia posible es precio de hoy menos ese mínimo.
</details>

---

### Sábado 2 · 2 h · Algoritmos + carrera

**Algoritmos (1 h). Longest Substring Without Repeating Characters** (Medium) → `practice/algoritmos/longest_substring.py`

~~~python
def length_of_longest_substring(s: str) -> int:
    ...


if __name__ == "__main__":
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    print("OK")
~~~

<details>
<summary>Pista</summary>
Una ventana [izquierda, derecha] sin repetidos y un conjunto con sus letras. Al encontrar una repetida, mueve la izquierda hasta que deje de estar repetida.
</details>

**Carrera (1 h):**

1. **4 historias STAR más** (40 min), en el mismo sitio privado que las de la semana pasada:
    - Un conflicto en un trabajo de grupo del máster y cómo lo resolviste.
    - Un error tuyo: qué pasó, qué hiciste y qué cambiaste después.
    - El Tableau de Walmart con el plazo justo: cómo priorizaste.
    - Una decisión técnica con datos (por ejemplo, en el PSO, por qué la vectorización ganó al multiproceso).
2. **CV** (20 min): en la línea de skills añade *Docker* y *FastAPI*. En proyectos, una línea para el CLI con el enlace al repo. Mantén tu formato y una sola página.

---

### Domingo 3 · 15 min · Cierre

1. En el `README.md` principal, pon el proyecto 02 DocuChat en **In progress**.
2. Log semanal.
3. En Claude Code:
    ```
    Cerramos la semana 10. Revisa el checklist de resources/semanas/semana-10.md,
    ejecuta los tests de projects/02-docuchat y dime qué falta. Luego commit,
    push de semana10-docuchat-ingesta, PR, mergea y deja main al día.
    ```

---

📦 **Entregable:** `projects/02-docuchat` con ingesta de PDFs, búsqueda semántica y tests de chunking.

✅ **Checklist**
- [ ] Subo un PDF y se guardan sus chunks con página y embedding
- [ ] `/search` encuentra fragmentos por significado
- [ ] Los 5 tests de `trocear` pasan
- [ ] Índice HNSW creado y visto en `EXPLAIN`
- [ ] Sé explicar las dos fases de un RAG y por qué se trocea con solapamiento
- [ ] 2 problemas de algoritmos; 8 historias STAR en total; CV actualizado

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `expected 768 dimensions, not 3072` | El modelo ignoró `dimensions` y devuelve 3072. No subas `embedding_dim` a 3072: el índice HNSW admite como máximo 2000. Busca en la documentación de Gemini cómo pedir menos dimensiones o usa otro modelo de embeddings. |
| `Form data requires "python-multipart"` | Falta `uv add python-multipart`. |
| `pypdf` devuelve texto vacío | El PDF es una imagen escaneada, sin texto. Usa otro PDF; el OCR queda fuera del alcance de v0. |
| La subida tarda mucho | Es la llamada de embeddings. Normal con PDFs grandes; prueba primero con uno de 5–10 páginas. |
| `relation "chunks" does not exist` | No se ejecutó `init_db()`. Arranca la API (lo hace en `lifespan`) o ejecútalo a mano. |
| Error 429 al subir varios PDFs seguidos | Has superado la cuota por minuto. Espera un minuto o baja `LOTE` a 20. |
