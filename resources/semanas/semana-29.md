# Semana 29 · 10–16 may · Integraciones: webhook, cola y notificación

[← Semana 28](semana-28.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 30 →](semana-30.md)

🎯 **Objetivo:** el día a día de un FDE es conectar sistemas que no se conocen. Esta semana, cuando se crea un ticket en el CRM, **llega solo** a tu sistema (webhook firmado), se encola, un proceso aparte lo analiza con las políticas de TechStore y avisa al equipo en Slack. Sin duplicados aunque el aviso llegue dos veces, y con reintentos si algo falla.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 11 | 1 h | Técnico | Webhook firmado del CRM y receptor (la firma la verificas tú) |
| Miércoles 12 | 1 h | Algoritmos | 2 Medium de repaso |
| Jueves 13 | 1 h | Técnico | Cola en Redis y worker con idempotencia y reintentos |
| Sábado 15 | 1,5 h | Técnico + carrera | Triaje con IA + aviso a Slack (30 min) + 2 candidaturas (1 h) |
| Domingo 16 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

```
CRM ──webhook firmado──▶ receptor (/webhooks/ticket) ──▶ cola (Redis) ──▶ worker ──▶ triaje IA ──▶ Slack
        (ticket creado)     responde 202 al momento                         │
                                                                             └─ falla → reintento (máx. 3) → cola de muertos
```

- **Webhook:** en lugar de preguntar cada minuto "¿hay tickets nuevos?" (*polling*), el CRM te **avisa** con una petición HTTP cuando pasa algo.
- **Firma HMAC:** cualquiera podría llamar a tu URL de webhook. El CRM firma el contenido con un secreto compartido; tú recalculas la firma y, si no coincide, rechazas la petición. Así funcionan Stripe, GitHub o Slack.
- **Responder rápido y encolar:** el que manda el webhook espera unos segundos como mucho. Respondes `202 Accepted` al momento y el trabajo lento (el LLM) lo hace otro proceso, el **worker**, leyendo de una **cola**.
- **Idempotencia:** los webhooks pueden llegar dos veces (reintentos de red). Procesar dos veces = dos avisos o dos respuestas al cliente. Se evita marcando cada ticket como procesado de forma atómica.
- **Reintentos y cola de muertos (*dead letter queue*):** si algo falla, se reintenta. Tras 3 fallos, el trabajo va a una cola aparte para revisarlo a mano, en lugar de reintentar para siempre.
- **Workflow, no agente:** el triaje siempre hace lo mismo (buscar políticas → resumir → sugerir respuesta). Como viste en la semana 24, aquí un workflow es mejor que un agente: más barato y predecible.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana29-integraciones
cd projects/03-support-agent
uv add redis
```

Añade Redis al `docker-compose.yml` del proyecto, debajo de `db`:

```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

```bash
docker compose up -d
```

En el `.env` de la raíz del repo:

```
WEBHOOK_SECRET=pon-aqui-una-cadena-larga-y-aleatoria
WEBHOOK_URL=http://localhost:8002/webhooks/ticket
REDIS_URL=redis://localhost:6379/0
```

---

### Martes 11 · 1 h · Webhook firmado

**Paso 1 · El CRM avisa (15 min).** En `mock_crm/main.py`:

~~~python
import hashlib
import hmac
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secreto-local")


def firmar(cuerpo: bytes, secreto: str = WEBHOOK_SECRET) -> str:
    return hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


def notificar(ticket: dict) -> None:
    """Envía el webhook. Si el receptor no está, no rompe el CRM."""
    if not WEBHOOK_URL:
        return
    cuerpo = json.dumps({"evento": "ticket.creado", "ticket": ticket}, ensure_ascii=False).encode()
    try:
        httpx.post(WEBHOOK_URL, content=cuerpo, timeout=5,
                   headers={"Content-Type": "application/json", "X-Firma": firmar(cuerpo)})
    except httpx.HTTPError:
        pass
~~~

Y cambia el endpoint de crear ticket para que avise **después** de responder:

~~~python
@app.post("/tickets", status_code=201)
def crear_ticket(ticket: TicketIn, tareas: BackgroundTasks):
    _cliente(ticket.cliente_id)
    nuevo = {"id": len(TICKETS) + 1, "estado": "abierto", "comentarios": [], **ticket.model_dump()}
    TICKETS[nuevo["id"]] = nuevo
    tareas.add_task(notificar, nuevo)  # se ejecuta tras devolver la respuesta
    return nuevo
~~~

**Paso 2 · El receptor (35 min).** Crea `agent/webhooks.py`. La función `verificar_firma` la escribes tú:

~~~python
"""Recibe webhooks del CRM, verifica la firma y encola el trabajo."""
import hashlib
import hmac
import json
import os

import redis
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request

load_dotenv()
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secreto-local")
cola = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)

app = FastAPI(title="Webhooks del agente de soporte")


def verificar_firma(cuerpo: bytes, firma: str, secreto: str) -> bool:
    # TODO: calcula el HMAC-SHA256 de `cuerpo` con `secreto` (como en firmar() del CRM)
    #       y compáralo con `firma` usando hmac.compare_digest (NO con ==).
    raise NotImplementedError


@app.post("/webhooks/ticket", status_code=202)
async def recibir_ticket(request: Request, x_firma: str = Header(default="")):
    cuerpo = await request.body()  # el cuerpo tal cual llegó: la firma se calculó sobre esos bytes
    if not verificar_firma(cuerpo, x_firma, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Firma no válida")
    evento = json.loads(cuerpo)
    cola.lpush("cola:tickets", json.dumps({"ticket": evento["ticket"], "intentos": 0}))
    return {"encolado": True}
~~~

**¿Por qué `compare_digest` y no `==`?** `==` deja de comparar en la primera letra distinta, y midiendo tiempos un atacante podría adivinar la firma letra a letra. `compare_digest` tarda siempre lo mismo.

<details>
<summary>Solución</summary>

~~~python
def verificar_firma(cuerpo: bytes, firma: str, secreto: str) -> bool:
    esperada = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperada, firma)
~~~
</details>

Tests en `tests/test_webhooks.py`:

~~~python
import hashlib
import hmac

from agent.webhooks import verificar_firma


def firma(cuerpo: bytes, secreto: str) -> str:
    return hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()


def test_firma_correcta():
    assert verificar_firma(b'{"a":1}', firma(b'{"a":1}', "s"), "s")


def test_cuerpo_alterado():
    assert not verificar_firma(b'{"a":2}', firma(b'{"a":1}', "s"), "s")


def test_secreto_distinto():
    assert not verificar_firma(b'{"a":1}', firma(b'{"a":1}', "otro"), "s")
~~~

**Prueba de punta a punta:**

```bash
# terminal 1
uv run uvicorn mock_crm.main:app --port 8001
# terminal 2
uv run uvicorn agent.webhooks:app --port 8002
# terminal 3: crear un ticket y mirar la cola
curl -s -X POST localhost:8001/tickets -H "Content-Type: application/json" \
  -d '{"cliente_id": 1, "asunto": "El portátil no enciende", "prioridad": "media"}'
docker compose exec redis redis-cli LRANGE cola:tickets 0 -1
```

**Está bien si** el ticket aparece en la cola. Y si mandas un webhook sin firma (`curl -X POST localhost:8002/webhooks/ticket -d '{}'`), recibes 401.

```bash
uv run pytest -v
git add -A && git commit -m "Support agent: webhook firmado del CRM y receptor"
```

---

### Miércoles 12 · 1 h · Algoritmos

Elige 2 Medium de temas distintos que te costaran (mira el README de algoritmos) y repítelos en 25 minutos cada uno, sin mirar. Si te sobra tiempo, empieza **Daily Temperatures** (patrón Stack) de NeetCode.

---

### Jueves 13 · 1 h · Worker con idempotencia y reintentos

Crea `agent/worker.py`. La parte de idempotencia y reintentos la escribes tú:

~~~python
"""Worker: saca tickets de la cola, los analiza y avisa. Sin duplicados y con reintentos."""
import json
import os

import redis
from dotenv import load_dotenv

load_dotenv()
cola = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
MAX_INTENTOS = 3


def procesar(ticket: dict) -> None:
    """Por ahora solo imprime; el sábado añadirás el triaje con IA y Slack."""
    print(f"Procesando ticket {ticket['id']}: {ticket['asunto']}")


def manejar(trabajo: dict) -> None:
    ticket_id = trabajo["ticket"]["id"]
    # TODO 1 · Idempotencia:
    #   cola.set(f"procesado:{ticket_id}", "1", nx=True, ex=7 * 24 * 3600)
    #   devuelve False si la clave ya existía → si es así, imprime "duplicado" y return
    # TODO 2 · Procesar con reintentos:
    #   try: procesar(trabajo["ticket"])
    #   except Exception as error:
    #       - borra la marca procesado:{id} (no se completó)
    #       - suma 1 a trabajo["intentos"]
    #       - si intentos < MAX_INTENTOS → vuelve a meterlo en "cola:tickets"
    #         si no → mételo en "cola:muertos" e imprime el error
    raise NotImplementedError


if __name__ == "__main__":
    print("Worker esperando tickets…")
    while True:
        _, dato = cola.brpop("cola:tickets")  # bloquea hasta que llega algo
        manejar(json.loads(dato))
~~~

<details>
<summary>Solución de manejar</summary>

~~~python
def manejar(trabajo: dict) -> None:
    ticket_id = trabajo["ticket"]["id"]
    if not cola.set(f"procesado:{ticket_id}", "1", nx=True, ex=7 * 24 * 3600):
        print(f"Ticket {ticket_id} duplicado: lo ignoro")
        return
    try:
        procesar(trabajo["ticket"])
    except Exception as error:
        cola.delete(f"procesado:{ticket_id}")
        trabajo["intentos"] += 1
        destino = "cola:tickets" if trabajo["intentos"] < MAX_INTENTOS else "cola:muertos"
        cola.lpush(destino, json.dumps(trabajo))
        print(f"Ticket {ticket_id} falló ({error}); intento {trabajo['intentos']} → {destino}")
~~~
</details>

**Pruebas (20 min)** con las 3 terminales de antes más una cuarta con `uv run python -m agent.worker`:

1. **Normal:** crea un ticket → el worker lo procesa.
2. **Duplicado:** copia el trabajo que está en la cola y mételo dos veces a mano:

    ```bash
    docker compose exec redis redis-cli LPUSH cola:tickets '{"ticket": {"id": 99, "asunto": "prueba"}, "intentos": 0}'
    docker compose exec redis redis-cli LPUSH cola:tickets '{"ticket": {"id": 99, "asunto": "prueba"}, "intentos": 0}'
    ```

    → el segundo debe decir "duplicado".
3. **Fallo:** pon temporalmente `raise RuntimeError("fallo de prueba")` dentro de `procesar` y crea un ticket → 3 intentos y acaba en `cola:muertos` (`redis-cli LRANGE cola:muertos 0 -1`). Después quita el `raise`.

```bash
git add -A && git commit -m "Support agent: worker con idempotencia, reintentos y cola de muertos"
```

---

### Sábado 15 · 1,5 h

**Técnico, 30 min · Triaje con IA y Slack.**

1. **Slack (10 min):** crea un workspace gratuito, una app en api.slack.com/apps → *Incoming Webhooks* → actívalo y añade uno al canal `#soporte`. Copia la URL al `.env` como `SLACK_WEBHOOK_URL`. Si no quieres usar Slack, Discord tiene webhooks equivalentes.
2. **Triaje (20 min).** Sustituye `procesar` en `agent/worker.py`:

    ~~~python
    import httpx
    from openai import OpenAI

    llm = OpenAI(api_key=os.environ["GOOGLE_API_KEY"],
                 base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

    TRIAJE = """Eres el asistente de triaje del equipo de soporte de TechStore.
    Con el ticket y las políticas, devuelve exactamente:
    Categoría: (envío / producto dañado / devolución / garantía / otro)
    Prioridad sugerida: (baja / media / alta) y por qué en 5 palabras
    Respuesta sugerida al cliente: máximo 3 frases, basada SOLO en las políticas."""


    def buscar_politicas(texto: str) -> str:
        r = httpx.get(f"{os.environ['DOCUCHAT_URL']}/search", params={"q": texto, "k": 3},
                      headers={"X-API-Key": os.environ["DOCUCHAT_API_KEY"]}, timeout=30)
        r.raise_for_status()  # si falla, salta la excepción y entra el reintento
        return "\n".join(f"[pág. {f['page']}] {f['text']}" for f in r.json())


    def procesar(ticket: dict) -> None:
        politicas = buscar_politicas(ticket["asunto"])
        triaje = llm.chat.completions.create(
            model="gemini-3.8-flash", temperature=0,
            messages=[{"role": "system", "content": TRIAJE},
                      {"role": "user", "content": f"Ticket: {json.dumps(ticket, ensure_ascii=False)}\n\nPolíticas:\n{politicas}"}],
        ).choices[0].message.content
        texto = f"*Nuevo ticket #{ticket['id']}* (cliente {ticket['cliente_id']}): {ticket['asunto']}\n{triaje}"
        httpx.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": texto}, timeout=10).raise_for_status()
        print(f"Ticket {ticket['id']} enviado a Slack")
    ~~~

3. **Pruébalo:** con todo arrancado, crea un ticket "El monitor llegó con la pantalla rota" → en `#soporte` debe aparecer la categoría, la prioridad y una respuesta sugerida que mencione la foto en 48 h de tus políticas.

Añade al README del proyecto 03 una sección **Integrations** con el diagrama de arriba.

**Carrera, 1 h · 2 candidaturas.** Si alguna es de FDE, esta semana es tu mejor ejemplo: "conecté un CRM con un agente mediante webhooks firmados, una cola con idempotencia y notificaciones a Slack".

---

### Domingo 16 · 15 min · Cierre

Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] El CRM manda webhooks firmados al crear tickets
- [ ] Firma verificada con `compare_digest` y 3 tests
- [ ] El receptor responde 202 y encola
- [ ] Duplicados ignorados; fallos reintentados 3 veces y luego a `cola:muertos`
- [ ] Triaje con las políticas y aviso en Slack
- [ ] 2 problemas de repaso y 2 candidaturas

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| El receptor siempre da 401 | Los dos procesos tienen que leer el mismo `WEBHOOK_SECRET` del `.env`. Si en el CRM sale "secreto-local", no está cargando el `.env`. |
| La firma no cuadra aunque el secreto sea igual | Firma y verificación deben usar **los mismos bytes**. No vuelvas a serializar el JSON antes de verificar: usa `await request.body()`. |
| El worker no recibe nada | `redis-cli LRANGE cola:tickets 0 -1`: si está vacío, el webhook no llega (mira la terminal del receptor). |
| `KeyError: SLACK_WEBHOOK_URL` | Falta en el `.env` o no reiniciaste el worker. |
