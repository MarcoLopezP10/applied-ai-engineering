# Semana 9 · 21–27 dic · Docker + pgvector + embeddings

[← Semana 8](semana-08.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 10 →](semana-10.md)

🎯 **Objetivo:** saber meter una API y una base de datos en contenedores, y entender cómo se busca texto **por significado** con embeddings y pgvector. Es la base de DocuChat, que empiezas la semana que viene.

**Navidad: unas 10 h esta semana.** Libres el 24 y el 25.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Lunes 21 | 2,5 h | Técnico | Docker desde cero + tu primera imagen |
| Martes 22 | 2,5 h | Técnico | Docker Compose: API + Postgres |
| Miércoles 23 | 2 h + 1 h | Técnico + algoritmos | pgvector y embeddings + 3Sum |
| Sábado 26 | 2 h | Algoritmos + carrera | Container With Most Water + 4 historias STAR |
| Domingo 27 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**Docker.** Empaqueta tu aplicación con todo lo que necesita (Python, librerías, configuración) para que funcione igual en tu Mac, en el de un compañero y en un servidor de AWS. Es lo que separa "en mi ordenador funciona" de "está en producción".

- **Imagen:** la receta congelada (como una clase).
- **Contenedor:** una imagen en ejecución (como un objeto de esa clase). Puedes tener varios de la misma imagen.
- **Dockerfile:** el archivo con las instrucciones para construir la imagen. Cada línea crea una **capa**; Docker reutiliza las que no han cambiado, por eso el orden importa.
- **Volumen:** una carpeta que sobrevive aunque borres el contenedor. Ahí vive la base de datos.
- **Docker Compose:** levanta varios contenedores a la vez (API + base de datos) con un solo comando. Dentro de Compose, cada servicio se encuentra por su **nombre** (la API se conecta a `db`, no a `localhost`).

**Embeddings.** Un modelo convierte un texto en una lista de números (por ejemplo, 768) que representa su **significado**. Dos textos que dicen lo mismo con palabras distintas tienen vectores parecidos. "Me duele la cabeza" y "tengo migraña" quedan cerca; "me duele la cabeza" y "el Real Madrid ganó" quedan lejos.

**Distancia coseno.** Mide cuánto apuntan dos vectores en la misma dirección: 0 significa el mismo significado y 1 que no tienen relación. En pgvector se escribe con el operador `<=>`.

**pgvector.** Una extensión de PostgreSQL que añade el tipo `vector` y la búsqueda de vecinos más cercanos. Te permite usar la base de datos que ya conoces del TFG (Supabase es Postgres) en lugar de aprender otra.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana9-docker-pgvector
mkdir -p practice/semana9/api
```

Abre **Docker Desktop** y espera a que diga "Engine running".

---

### Lunes 21 · 2,5 h · Docker desde cero

**Paso 1 · Primeros comandos (30 min).** Ejecútalos uno a uno y lee lo que sale:

```bash
docker run hello-world                       # descarga una imagen y la ejecuta
docker run -it --rm python:3.11-slim python  # un Python dentro de un contenedor (sal con exit())
docker images                                # imágenes que tienes descargadas
docker ps -a                                 # contenedores (-a incluye los parados)
```

Pregúntate: ¿por qué el segundo comando tarda la primera vez y no la segunda? (Respuesta: la imagen ya está descargada.)

**Paso 2 · Lectura (45 min).** Lee la semana 6 del roadmap técnico (`resources/ai-engineer-roadmap-48weeks.md`, "Semana 6: Docker Basics") hasta la parte de Compose, sin hacer todavía su ejercicio.

**Paso 3 · Tu primera imagen (75 min).**

1. Copia tu API de la semana 2: `cp practice/semana2/miniCRUD_API.py practice/semana9/api/main.py`.
2. Añade al final de `main.py` un endpoint de salud (lo usan todos los servidores para saber si la app está viva):

~~~python
@app.get("/health")
def health():
    return {"status": "ok"}
~~~

3. Crea `practice/semana9/api/requirements.txt`:

```
fastapi
uvicorn[standard]
psycopg[binary]
```

4. Crea `practice/semana9/api/Dockerfile` y lee los comentarios:

```dockerfile
# Imagen base: Python 3.11 en versión ligera
FROM python:3.11-slim

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Primero solo las dependencias: si cambias el código pero no requirements.txt,
# Docker reutiliza esta capa y no reinstala nada (builds mucho más rápidos)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Después el código
COPY main.py .

# Puerto en el que escucha la app
EXPOSE 8000

# 0.0.0.0 para que se pueda acceder desde fuera del contenedor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

5. Construye y ejecuta:

```bash
cd practice/semana9/api
docker build -t crud-api .
docker run --rm -p 8000:8000 crud-api
```

**Está bien si** abres http://localhost:8000/health y ves `{"status":"ok"}`, y en http://localhost:8000/docs ves tu API. Para pararlo, pulsa Ctrl+C.

6. **Experimento de capas:** cambia un texto en `main.py`, vuelve a hacer `docker build` y fíjate en que la línea de `pip install` sale como `CACHED`.

```bash
cd ../../..
git add practice/semana9 && git commit -m "Semana 9: API en Docker"
```

---

### Martes 22 · 2,5 h · Docker Compose: API + Postgres

**Paso 1 · Que la API hable con la base de datos (30 min).** Añade a `practice/semana9/api/main.py`:

~~~python
import os

import psycopg


@app.get("/db-check")
def db_check():
    """Comprueba que la API llega a la base de datos."""
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        version = conn.execute("SELECT version()").fetchone()[0]
    return {"db": "ok", "version": version}
~~~

**Paso 2 · El `docker-compose.yml` (45 min).** Crea `practice/semana9/docker-compose.yml`:

```yaml
services:
  db:
    image: pgvector/pgvector:pg16      # Postgres 16 con pgvector ya instalado
    environment:
      POSTGRES_USER: marco
      POSTGRES_PASSWORD: marco
      POSTGRES_DB: practicas
    ports:
      - "5432:5432"                    # para conectarte desde tu Mac
    volumes:
      - pgdata:/var/lib/postgresql/data  # los datos sobreviven a docker compose down
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U marco -d practicas"]
      interval: 5s
      retries: 10

  api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      # Ojo: el host es "db" (el nombre del servicio), no "localhost"
      DATABASE_URL: postgresql://marco:marco@db:5432/practicas
    depends_on:
      db:
        condition: service_healthy     # espera a que la BD esté lista

volumes:
  pgdata:
```

Estas contraseñas solo valen para tu ordenador. En producción irán en variables de entorno secretas (lo verás en la semana 17).

**Paso 3 · Levantarlo (30 min):**

```bash
cd practice/semana9
docker compose up --build
```

**Está bien si** http://localhost:8000/db-check devuelve `"db": "ok"` y la versión de PostgreSQL.

Prueba también estos comandos en otra terminal:

```bash
docker compose ps            # qué está corriendo
docker compose logs api      # los logs de la API
docker compose down          # parar (los datos se quedan en el volumen)
docker compose down -v       # parar y BORRAR los datos
```

**Paso 4 · Entender, no solo copiar (45 min).** Sin mirar nada, escribe en `practice/semana9/NOTAS.md` cinco frases con tus palabras: qué es una imagen, qué es un contenedor, para qué sirve un volumen, por qué la API usa `db` y no `localhost`, y por qué se copia `requirements.txt` antes que el código. Te lo preguntarán en entrevistas.

```bash
cd ../..
git add practice/semana9 && git commit -m "Semana 9: Docker Compose con API y Postgres"
```

---

### Miércoles 23 · 3 h · pgvector y embeddings + algoritmos

**Paso 1 · pgvector a mano (30 min).** Con `docker compose up -d` en marcha (dentro de `practice/semana9`), abre una consola SQL:

```bash
docker compose exec db psql -U marco -d practicas
```

Pega esto. Son vectores de juguete de 3 dimensiones: la primera dice "rojo", la segunda "amarillo" y la tercera "ácido":

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE frutas (id serial PRIMARY KEY, nombre text, embedding vector(3));
INSERT INTO frutas (nombre, embedding) VALUES
  ('fresa',   '[0.9, 0.1, 0.2]'),
  ('cereza',  '[0.95, 0.05, 0.1]'),
  ('plátano', '[0.1, 0.9, 0.05]'),
  ('limón',   '[0.1, 0.8, 0.9]');

-- ¿Qué se parece más a "algo rojo y poco ácido"?
SELECT nombre, embedding <=> '[0.9, 0.1, 0.1]' AS distancia
FROM frutas ORDER BY distancia LIMIT 2;
```

**Está bien si** salen fresa y cereza con distancias cercanas a 0. Sal con `\q`.

**Paso 2 · Embeddings reales (90 min).** Ahora los vectores los genera Gemini a partir de frases. En la raíz del repo:

```bash
uv add "psycopg[binary]" pgvector numpy
```

Crea `practice/semana9/embeddings_demo.py`. Todo está hecho menos la función `buscar`, que escribes tú:

~~~python
"""Semana 9 · Búsqueda por significado con embeddings de Gemini y pgvector."""
import os

import numpy as np
import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from pgvector.psycopg import register_vector

load_dotenv()

# Comprueba el nombre actual del modelo de embeddings en la documentación de Gemini
EMBEDDING_MODEL = "gemini-embedding-001"
DIMENSIONES = 768  # pedimos 768: suficiente, más barato de guardar y se puede indexar
DB_URL = "postgresql://marco:marco@localhost:5432/practicas"

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

FRASES = [
    "El Real Madrid ganó la final en el último minuto.",
    "El base del equipo anotó 30 puntos en el partido.",
    "Para el gazpacho hace falta tomate, pepino y aceite.",
    "La paella valenciana lleva arroz, pollo y conejo.",
    "Python es un lenguaje muy usado en ciencia de datos.",
    "FastAPI permite crear APIs REST en pocas líneas.",
    "Docker empaqueta una aplicación con sus dependencias.",
    "Un índice HNSW acelera la búsqueda de vecinos cercanos.",
    "Lisboa tiene tranvías amarillos y miradores preciosos.",
    "En Kioto hay templos y jardines de estilo zen.",
    "Los tipos de interés del BCE afectan a las hipotecas.",
    "Diversificar la cartera reduce el riesgo de inversión.",
    "Mi abuela olvida tomarse las pastillas por la mañana.",
    "Una alarma con voz ayuda a recordar la medicación.",
    "El examen de estadística entra hasta el tema cinco.",
    "La regresión lineal predice un valor numérico.",
    "Hoy hace sol y 20 grados en Madrid.",
    "Mañana lloverá en todo el norte de España.",
    "El portátil se calienta cuando entreno modelos.",
    "Necesito más memoria RAM para cargar el dataset.",
]


def embed(textos: list[str]) -> list[np.ndarray]:
    """Convierte textos en vectores de DIMENSIONES números."""
    respuesta = client.embeddings.create(model=EMBEDDING_MODEL, input=textos, dimensions=DIMENSIONES)
    return [np.array(d.embedding) for d in respuesta.data]


def preparar_tabla(conn) -> None:
    conn.execute("DROP TABLE IF EXISTS frases")
    conn.execute(f"CREATE TABLE frases (id serial PRIMARY KEY, texto text, embedding vector({DIMENSIONES}))")
    for texto, vector in zip(FRASES, embed(FRASES)):
        conn.execute("INSERT INTO frases (texto, embedding) VALUES (%s, %s)", (texto, vector))


def buscar(conn, pregunta: str, k: int = 3) -> list[tuple[str, float]]:
    # TODO: 1) calcula el embedding de la pregunta con embed([pregunta])
    #       2) consulta SQL: texto y distancia coseno (<=>) con ese vector,
    #          ordenado de menor a mayor distancia, LIMIT k
    #       3) devuelve la lista de (texto, distancia)
    raise NotImplementedError


def main() -> None:
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)  # enseña a psycopg a mandar y recibir vectores
        preparar_tabla(conn)
        print(f"{len(FRASES)} frases guardadas. Pregunta lo que quieras (Enter vacío para salir).")
        while pregunta := input("\nPregunta: ").strip():
            for texto, distancia in buscar(conn, pregunta):
                print(f"  {distancia:.3f}  {texto}")


if __name__ == "__main__":
    main()
~~~

<details>
<summary>Solución de buscar</summary>

~~~python
def buscar(conn, pregunta: str, k: int = 3) -> list[tuple[str, float]]:
    [vector] = embed([pregunta])
    return conn.execute(
        "SELECT texto, embedding <=> %s AS distancia FROM frases ORDER BY distancia LIMIT %s",
        (vector, k),
    ).fetchall()
~~~
</details>

Ejecuta `uv run python practice/semana9/embeddings_demo.py` y prueba estas preguntas, que **no comparten palabras** con las frases:

- "deporte con pelota"
- "comida típica española"
- "cómo no olvidar los medicamentos" (fíjate: es tu TFG)
- "qué tiempo va a hacer"

**Está bien si** las 3 primeras de cada búsqueda son del tema correcto. Apunta en `NOTAS.md` la distancia típica de un acierto y la de un fallo.

> Si la API da error con `dimensions`, quita ese parámetro y pon en `DIMENSIONES` el tamaño real del vector (`len(d.embedding)`). Para esta demo no importa; en DocuChat necesitarás 2000 o menos para poder crear el índice.

**Paso 3 · Algoritmos (1 h).** **3Sum** (Medium) → `practice/algoritmos/three_sum.py`

~~~python
def three_sum(nums: list[int]) -> list[list[int]]:
    ...


if __name__ == "__main__":
    assert sorted(map(sorted, three_sum([-1, 0, 1, 2, -1, -4]))) == [[-1, -1, 2], [-1, 0, 1]]
    assert three_sum([0, 1, 1]) == []
    assert three_sum([0, 0, 0]) == [[0, 0, 0]]
    print("OK")
~~~

<details>
<summary>Pista</summary>
Ordena la lista. Fija un número y busca los otros dos con dos punteros (uno al principio y otro al final de lo que queda). Sáltate los repetidos para no duplicar tríos.
</details>

```bash
git add -A && git commit -m "Semana 9: pgvector, embeddings y 3Sum"
```

---

### Sábado 26 · 2 h · Algoritmos + historias STAR

**Algoritmos (1 h). Container With Most Water** (Medium) → `practice/algoritmos/container_most_water.py`

~~~python
def max_area(height: list[int]) -> int:
    ...


if __name__ == "__main__":
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
    assert max_area([1, 1]) == 1
    print("OK")
~~~

<details>
<summary>Pista</summary>
Dos punteros en los extremos. El agua la limita la pared más baja: mueve siempre ese puntero, porque mover el otro nunca puede mejorar el área.
</details>

**Carrera (1 h) · 4 historias STAR.** Escríbelas en tu doc privado o en un documento de tu ordenador, **no en el repo**. En inglés, con un máximo de 150 palabras cada una:

| Parte | Qué cuenta | Peso |
|---|---|:---:|
| **S**ituation | Contexto en 1–2 frases | 10 % |
| **T**ask | Qué te tocaba a ti | 10 % |
| **A**ction | Qué hiciste **tú** (en primera persona, no "el equipo") | 60 % |
| **R**esult | Qué pasó, con un número si puede ser | 20 % |

Las 4 de hoy:

1. **TFG (app de recordatorios médicos):** problema de usuario, decisiones de accesibilidad, test con más de 5 usuarios y qué cambiaste tras su feedback.
2. **PSO paralelo:** cómo mediste el coste del GIL y de la comunicación entre procesos, qué estrategia ganó y por qué. Termina con la matrícula de honor.
3. **Capitán de baloncesto:** una situación concreta de liderazgo (un conflicto, una mala racha, un compañero desmotivado).
4. **Voluntariado A LA PAR:** coordinar a más de 5 voluntarios con personas con discapacidad intelectual; qué organizaste y qué aprendiste.

Léelas en voz alta: si una tarda más de 2 minutos, recórtala.

---

### Domingo 27 · 15 min · Cierre

1. Añade la semana 9 a `practice/README.md`:
    ```markdown
    ## Week 9: Docker, pgvector and embeddings

    - [`api/`](semana9/api): Week 2 API containerized, with health and database checks.
    - [`docker-compose.yml`](semana9/docker-compose.yml): API + PostgreSQL (pgvector) with healthcheck and persistent volume.
    - [`embeddings_demo.py`](semana9/embeddings_demo.py): semantic search over 20 sentences with Gemini embeddings and pgvector (cosine distance).
    ```
2. Log semanal.
3. En Claude Code:
    ```
    Cerramos la semana 9. Revisa el checklist de resources/semanas/semana-09.md
    y dime qué falta. Luego commit, push de semana9-docker-pgvector, PR,
    mergea y deja main al día.
    ```

---

📦 **Entregable:** `practice/semana9/` con `api/` (Dockerfile), `docker-compose.yml`, `embeddings_demo.py` y `NOTAS.md`.

✅ **Checklist**
- [ ] Sé explicar imagen, contenedor, volumen y capas
- [ ] `docker compose up` levanta la API y la BD, y `/db-check` responde
- [ ] La búsqueda por significado encuentra frases sin compartir palabras
- [ ] Sé qué mide la distancia coseno
- [ ] 3Sum y Container With Most Water
- [ ] 4 historias STAR

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop no está abierto. |
| `port is already allocated` en el 5432 | Ya tienes otro Postgres corriendo (quizá el de `projects/docker-compose.yml`). Páralo con `docker compose down` en esa carpeta o cambia el puerto a `"5433:5432"`. |
| La API dice `connection refused` al conectar con `db` | Dentro de Compose usa `db` como host. Desde tu Mac (scripts fuera de Docker) usa `localhost`. |
| `type "vector" does not exist` | Falta `CREATE EXTENSION vector;` o la imagen no es `pgvector/pgvector`. |
| `can't adapt type 'numpy.ndarray'` | Falta `register_vector(conn)`, y tiene que ir después de crear la extensión. |
| El build es lentísimo en tu Mac Intel | Normal la primera vez. Si se repite, comprueba que copias `requirements.txt` antes que el código. |
