# Semana 16 · 8–14 feb · Preparar DocuChat para producción

[← Semana 15](semana-15.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 17 →](semana-17.md)

🎯 **Objetivo:** que DocuChat aguante usuarios reales antes de subirlo a Internet: logs útiles, errores del modelo bien gestionados, cada usuario con su clave y sus documentos, límites de uso e integración continua (CI) en GitHub.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 9 | 1 h | Técnico | Logs estructurados y errores del modelo |
| Miércoles 10 | 1 h | Algoritmos | Invert Binary Tree y Maximum Depth |
| Jueves 11 | 1 h | Técnico | Usuarios con API key, documentos por usuario y límites |
| Sábado 13 | 1,5 h | Técnico + carrera | CI con GitHub Actions (30 min) + repo plantilla y 1 candidatura (1 h) |
| Domingo 14 | 15 min | Cierre | Log y PR |

Material de apoyo: roadmap técnico, semanas 21 y 33 (producción y autenticación).

---

### 📖 Qué vas a aprender

**Logs estructurados.** En producción los logs los lee una máquina (CloudWatch, Datadog…). En JSON se pueden filtrar: "todas las peticiones del usuario ana que tardaron más de 5 segundos".

**Fallar bien.** El modelo va a fallar (saturado, cuota o *timeout*). El SDK de OpenAI ya reintenta con espera creciente (`max_retries`). Si aun así falla, el usuario debe recibir un mensaje claro y un código 503, no un error 500 con una traza de Python.

**Autenticación mínima con API keys.** Para una demo con 5 usuarios no hace falta un sistema de login completo. Cada usuario tiene una clave larga y aleatoria; la API la lee de la cabecera `X-API-Key` y sabe quién es. Cada documento guarda su dueño y **cada uno solo busca en sus documentos**.

**Rate limiting.** Limitar peticiones por minuto protege tu factura: un bucle mal hecho de un usuario no puede gastarte 50 € en una tarde.

**CI (integración continua).** Cada push ejecuta los tests y el linter en GitHub. Si algo se rompe, lo ves en la PR antes de mergear.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana16-produccion
cd projects/02-docuchat && docker compose up -d
uv add --dev ruff
```

---

### Martes 9 · 1 h · Logs y errores

**Paso 1 · Logs en JSON (25 min).** Crea `app/logs.py`:

~~~python
"""Logs en una línea JSON por evento."""
import json
import logging
import sys
import time


class FormatoJSON(logging.Formatter):
    def format(self, registro: logging.LogRecord) -> str:
        datos = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(registro.created)),
            "level": registro.levelname,
            "msg": registro.getMessage(),
        }
        datos.update(getattr(registro, "extra_campos", {}))
        return json.dumps(datos, ensure_ascii=False)


def configurar_logs() -> logging.Logger:
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(FormatoJSON())
    logger = logging.getLogger("docuchat")
    logger.handlers = [manejador]
    logger.setLevel(logging.INFO)
    return logger


log = configurar_logs()
~~~

En `app/main.py`, añade un *middleware* que registre cada petición:

~~~python
import time

from fastapi import Request

from app.logs import log


@app.middleware("http")
async def registrar_peticion(request: Request, call_next):
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    log.info("request", extra={"extra_campos": {
        "method": request.method,
        "path": request.url.path,
        "status": respuesta.status_code,
        "ms": round((time.perf_counter() - inicio) * 1000),
        "user": getattr(request.state, "usuario", None),
    }})
    return respuesta
~~~

**Paso 2 · Errores del modelo (20 min).** En `app/llm.py`, en los dos clientes, cambia `OpenAI(...)` para que tengan `max_retries=3` y `timeout=30`. En `app/main.py`:

~~~python
import openai
from fastapi.responses import JSONResponse


@app.exception_handler(openai.APIError)
async def error_del_modelo(request: Request, exc: openai.APIError):
    log.error("llm_error", extra={"extra_campos": {"path": request.url.path, "error": type(exc).__name__}})
    return JSONResponse(
        status_code=503,
        content={"detail": "El modelo no está disponible ahora mismo. Inténtalo en un minuto."},
    )
~~~

**Paso 3 · Comprobar (15 min).** Arranca la API, haz una pregunta y mira la terminal: debe salir una línea JSON por petición. Pon temporalmente una API key falsa en el `.env`, pregunta y comprueba que recibes un **503 con el mensaje claro**. Después vuelve a poner la buena.

```bash
git add -A && git commit -m "DocuChat: logs JSON y errores del modelo como 503"
```

---

### Miércoles 10 · 1 h · Algoritmos (Trees)

Pon esto al principio de cada archivo de árboles:

~~~python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def desde_lista(valores):
    """[4, 2, 7, 1, 3, 6, 9] → árbol por niveles (None = hueco)."""
    if not valores:
        return None
    nodos = [TreeNode(v) if v is not None else None for v in valores]
    hijos = nodos[::-1]
    raiz = hijos.pop()
    for nodo in nodos:
        if nodo:
            if hijos:
                nodo.left = hijos.pop()
            if hijos:
                nodo.right = hijos.pop()
    return raiz


def por_niveles(raiz):
    salida, cola = [], [raiz]
    while cola:
        nodo = cola.pop(0)
        if nodo:
            salida.append(nodo.val)
            cola += [nodo.left, nodo.right]
    return salida
~~~

**Invert Binary Tree** (Easy) → `practice/algoritmos/invert_tree.py`

~~~python
def invert_tree(root):
    ...


if __name__ == "__main__":
    assert por_niveles(invert_tree(desde_lista([4, 2, 7, 1, 3, 6, 9]))) == [4, 7, 2, 9, 6, 3, 1]
    print("OK")
~~~

**Maximum Depth of Binary Tree** (Easy) → `practice/algoritmos/max_depth.py`

~~~python
def max_depth(root) -> int:
    ...


if __name__ == "__main__":
    assert max_depth(desde_lista([3, 9, 20, None, None, 15, 7])) == 3
    assert max_depth(None) == 0
    print("OK")
~~~

<details>
<summary>Pista para los dos</summary>
Recursión: resuelve el problema para el hijo izquierdo y para el derecho, y combina. ¿Cuál es el caso base?
</details>

---

### Jueves 11 · 1 h · Usuarios, documentos por usuario y límites

**Paso 1 · Claves y configuración (10 min).** Genera una clave para ti:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Añade a `.env` (en formato JSON, de clave a nombre de usuario):

```
API_KEYS={"la-clave-que-has-generado":"marco"}
```

En `Settings`:

~~~python
    api_keys: dict[str, str] = {}
    max_pdf_mb: int = 20
    peticiones_por_minuto: int = 20
~~~

**Paso 2 · Cada documento tiene dueño (15 min).** En `app/db.py`, añade a `Document`:

~~~python
    owner: Mapped[str] = mapped_column(String(100), default="marco", index=True)
~~~

Y en `init_db()`, para que la tabla que ya existe gane la columna:

~~~python
        conn.execute(text(
            "ALTER TABLE documents ADD COLUMN IF NOT EXISTS owner varchar(100) NOT NULL DEFAULT 'marco'"
        ))
~~~

> En un proyecto real, los cambios de esquema se hacen con migraciones (Alembic). Aquí basta con `ALTER ... IF NOT EXISTS`; menciónalo en el README como mejora pendiente.

**Paso 3 · Filtrar por dueño (15 min).** Añade un parámetro `owner: str | None = None` a `buscar`, `ids_vectorial`, `ids_texto` y `responder`, y pásalo de una función a otra. Si `owner` no es `None`, filtra:

- En las consultas con SQLAlchemy: `.join(Document).where(Document.owner == owner)`.
- En `ids_texto`: `JOIN documents d ON d.id = chunks.document_id` y `AND (:owner IS NULL OR d.owner = :owner)`, pasando `"owner": owner` en los parámetros.

Así los scripts de eval, que no pasan `owner`, siguen funcionando igual.

**Paso 4 · Quién eres y cuánto puedes pedir (20 min).** Crea `app/seguridad.py`. La clase `LimitadorPorMinuto` la escribes tú:

~~~python
"""Autenticación por API key y límite de peticiones por usuario."""
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request

from app.config import settings


class LimitadorPorMinuto:
    """Permite como máximo `maximo` peticiones por usuario en cada ventana de `ventana_s` segundos."""

    def __init__(self, maximo: int, ventana_s: float = 60.0):
        self.maximo = maximo
        self.ventana_s = ventana_s
        self.peticiones: dict[str, deque] = defaultdict(deque)

    def permitir(self, clave: str, ahora: float | None = None) -> bool:
        # TODO: 1) quita de la cola de `clave` las marcas de tiempo más viejas que la ventana
        #       2) si ya hay `maximo`, devuelve False
        #       3) si no, añade `ahora` y devuelve True
        raise NotImplementedError


limitador = LimitadorPorMinuto(settings.peticiones_por_minuto)


def usuario_actual(request: Request, x_api_key: str = Header(default="")) -> str:
    usuario = settings.api_keys.get(x_api_key)
    if not usuario:
        raise HTTPException(status_code=401, detail="API key no válida")
    if not limitador.permitir(usuario):
        raise HTTPException(status_code=429, detail="Demasiadas peticiones: espera un minuto")
    request.state.usuario = usuario  # para el log
    return usuario
~~~

<details>
<summary>Solución de permitir</summary>

~~~python
    def permitir(self, clave: str, ahora: float | None = None) -> bool:
        ahora = time.monotonic() if ahora is None else ahora
        cola = self.peticiones[clave]
        while cola and ahora - cola[0] >= self.ventana_s:
            cola.popleft()
        if len(cola) >= self.maximo:
            return False
        cola.append(ahora)
        return True
~~~
</details>

Tests en `tests/test_seguridad.py`:

~~~python
import os

os.environ.setdefault("GOOGLE_API_KEY", "clave-de-test")

from app.seguridad import LimitadorPorMinuto  # noqa: E402


def test_bloquea_al_superar_el_maximo():
    limitador = LimitadorPorMinuto(maximo=2)
    assert limitador.permitir("ana", ahora=0)
    assert limitador.permitir("ana", ahora=1)
    assert not limitador.permitir("ana", ahora=2)


def test_se_libera_al_pasar_la_ventana():
    limitador = LimitadorPorMinuto(maximo=1)
    assert limitador.permitir("ana", ahora=0)
    assert limitador.permitir("ana", ahora=61)


def test_cada_usuario_tiene_su_limite():
    limitador = LimitadorPorMinuto(maximo=1)
    assert limitador.permitir("ana", ahora=0)
    assert limitador.permitir("luis", ahora=0)
~~~

**Paso 5 · Proteger los endpoints.** En `app/main.py`, añade `usuario: str = Depends(usuario_actual)` a `/documents` (subir y listar), `/search` y `/ask`:

- Al subir, guarda `documento.owner = usuario` (pásalo a `ingestar_pdf`) y rechaza PDFs grandes:

    ~~~python
    contenido = file.file.read()
    if len(contenido) > settings.max_pdf_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"El PDF supera {settings.max_pdf_mb} MB")
    ~~~

- Al listar, filtra con `.where(Document.owner == usuario)`.
- En `/search` y `/ask`, pasa `owner=usuario`.

`/health` se queda sin autenticación: lo usará AWS para saber si la app está viva.

En `tests/test_generate.py`, el test del endpoint ahora necesita una clave. Añade al principio del test:

~~~python
    main.app.dependency_overrides[main.usuario_actual] = lambda: "test"
~~~

**Comprueba:** en `/docs`, cada endpoint protegido tiene ahora un campo `x-api-key`. O desde la terminal:

```bash
curl -s localhost:8000/documents                          # → 401
curl -s -H "X-API-Key: TU_CLAVE" localhost:8000/documents # → tu lista
```

```bash
uv run pytest -v
git add -A && git commit -m "DocuChat: API keys, documentos por usuario y límites"
```

---

### Sábado 13 · 1,5 h

**Técnico, 30 min · CI con GitHub Actions.** Crea en la **raíz del repo** `.github/workflows/docuchat-ci.yml`:

```yaml
name: DocuChat CI

on:
  push:
    paths: ["projects/02-docuchat/**", ".github/workflows/docuchat-ci.yml"]
  pull_request:
    paths: ["projects/02-docuchat/**"]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/02-docuchat
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run pytest -v
        env:
          GOOGLE_API_KEY: clave-de-ci   # los tests no llaman a la API
```

Antes de subirlo, en local: `uv run ruff check . --fix`. Lo que no arregle solo, arréglalo a mano. Lo más típico es `E402`: los `import` tienen que ir arriba del archivo, salvo los que ya llevan `# noqa: E402`.

Haz push. **Está bien si** en la pestaña **Actions** de GitHub sale el workflow en verde. Añade al README de DocuChat el *badge*:

```markdown
![CI](https://github.com/MarcoLopezP10/applied-ai-engineering/actions/workflows/docuchat-ci.yml/badge.svg)
```

**Carrera, 1 h:**

1. **Repo plantilla para pruebas técnicas (30 min).** Muchas startups te mandan un ejercicio para casa con 48–72 h de plazo. Crea un repo público `fastapi-starter` con un `/health`, un test, un `Dockerfile`, el workflow de CI y un README con secciones vacías (Decisions, How to run, What I'd improve). En GitHub → Settings, marca **Template repository**. El día que te llegue una prueba, empiezas con "Use this template".
2. **1 candidatura** (30 min).

---

### Domingo 14 · 15 min · Cierre

1. Log semanal.
2. En Claude Code:
    ```
    Cerramos la semana 16. Revisa el checklist de resources/semanas/semana-16.md,
    ejecuta ruff y los tests de DocuChat y dime qué falta. Luego commit, push de
    semana16-produccion, PR (comprueba que el CI pasa), mergea y deja main al día.
    ```

---

✅ **Checklist**
- [ ] Una línea JSON por petición, con usuario y milisegundos
- [ ] Un fallo del modelo devuelve 503 con mensaje claro
- [ ] Sin API key → 401; cada usuario solo ve y busca en sus documentos
- [ ] PDF grande → 413; demasiadas peticiones → 429
- [ ] 3 tests del limitador y CI en verde en GitHub
- [ ] 2 problemas de árboles
- [ ] Repo plantilla y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `api_keys` llega vacío | El valor de `.env` tiene que ser JSON válido, con comillas dobles: `API_KEYS={"clave":"marco"}`. |
| Todos los endpoints dan 401 en los tests | Falta el `dependency_overrides` de `usuario_actual`. |
| El CI falla en `uv sync` | Sube también `uv.lock` del proyecto. |
| El CI falla en `ruff` y en local no | Ejecuta `uv run ruff check .` desde `projects/02-docuchat`, igual que el CI. |
| El limitador "olvida" al reiniciar | Es esperado: vive en memoria. Con varios servidores se usaría Redis. Anótalo como limitación conocida. |
