# Semana 32 · 31 may – 6 jun · Desplegar el agente

[← Semana 31](semana-31.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 33 →](semana-33.md)

🎯 **Objetivo:** el agente de soporte en una URL pública, como DocuChat. Tendrá una API de chat con aprobación humana, el CRM simulado, el worker de webhooks y una pantalla de demo en tu web. Todo en el mismo servidor y detrás del mismo dominio.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 1 | 1 h | Técnico | API de chat del agente e imagen Docker |
| Miércoles 2 | 1 h | System design | DocuChat para 10.000 usuarios |
| Jueves 3 | 1 h | Técnico | Servicios en el servidor y ruta `/agent` |
| Sábado 5 | 1,5 h | Técnico + carrera | Pantalla de demo con aprobación (30 min) + 2 candidaturas (1 h) |
| Domingo 6 | 15 min | Cierre | Checkpoint, log y PR |

---

### 📖 Qué vas a aprender

**Una imagen, varios procesos.** La API del agente, el worker y el CRM usan el mismo código. Se construye **una** imagen y cada servicio la arranca con un comando distinto. Es lo habitual en empresas: menos imágenes que mantener.

**Rutas por prefijo.** Caddy manda `https://tu-dominio/agent/...` al agente y el resto a DocuChat. Un solo dominio y un solo certificado.

**Servicios internos.** El CRM y Redis **no** se publican en Internet: solo los ven los demás contenedores por su nombre (`crm`, `redis`). Exponer solo lo necesario es la regla básica de seguridad.

**Human-in-the-loop en una interfaz.** En la terminal aprobabas con "si/no". En una web, la API devuelve "aprobación pendiente" y la pantalla muestra botones de Aprobar y Rechazar. En una empresa, esa pantalla sería la del supervisor, no la del cliente; en la demo haces los dos papeles.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana32-despliegue-agente
cd projects/03-support-agent
```

> **Memoria del servidor:** DocuChat, el agente, el worker, el CRM, Redis y Caddy no caben en una t3.micro. Cambia la instancia a **t3.small** (EC2 → Stop → Actions → Instance settings → Change instance type → Start) y actualiza la IP en DuckDNS si cambia. Revisa el coste en tu presupuesto.

---

### Martes 1 · 1 h · API de chat e imagen

**Paso 1 · La API (35 min).** Crea `agent/api.py`:

~~~python
"""API del agente de soporte: chat con aprobación humana + receptor de webhooks."""
import json
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from agent.chat import DB_URI, MCP_SERVIDORES
from agent.graph import construir_grafo
from agent.webhooks import recibir_ticket

API_KEYS = json.loads(os.getenv("API_KEYS", "{}"))
CORS = json.loads(os.getenv("CORS_ORIGINS", '["http://localhost:5173"]'))
estado: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    tools_mcp = await MultiServerMCPClient(MCP_SERVIDORES).get_tools()
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        estado["grafo"] = construir_grafo(tools_extra=tools_mcp, checkpointer=checkpointer)
        yield


app = FastAPI(title="Agente de soporte TechStore", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=CORS, allow_methods=["*"], allow_headers=["*"])
app.post("/webhooks/ticket", status_code=202)(recibir_ticket)  # reutiliza el receptor de la semana 29


def comprobar_clave(x_api_key: str = Header(default="")) -> None:
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="API key no válida")


class Mensaje(BaseModel):
    mensaje: str = Field(min_length=1, max_length=1000)
    hilo: str | None = None


class Decision(BaseModel):
    aprobar: bool


def _config(hilo: str) -> dict:
    return {"configurable": {"thread_id": hilo}, "recursion_limit": 15}


def _salida(hilo: str, resultado: dict) -> dict:
    if "__interrupt__" in resultado:
        return {"hilo": hilo, "respuesta": None, "aprobacion_pendiente": resultado["__interrupt__"][0].value}
    return {"hilo": hilo, "respuesta": resultado["messages"][-1].content, "aprobacion_pendiente": None}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", dependencies=[Depends(comprobar_clave)])
async def chat(m: Mensaje):
    hilo = m.hilo or str(uuid.uuid4())[:8]
    resultado = await estado["grafo"].ainvoke({"messages": [("user", m.mensaje)]}, _config(hilo))
    return _salida(hilo, resultado)


@app.post("/chat/{hilo}/decision", dependencies=[Depends(comprobar_clave)])
async def decidir(hilo: str, d: Decision):
    resultado = await estado["grafo"].ainvoke(Command(resume="si" if d.aprobar else "no"), _config(hilo))
    return _salida(hilo, resultado)
~~~

Pruébala en local (CRM, Redis y Postgres del agente arrancados; añade `API_KEYS` al `.env` de la raíz si no está):

```bash
uv run uvicorn agent.api:app --port 8002
curl -s -X POST localhost:8002/chat -H "X-API-Key: TU_CLAVE" -H "Content-Type: application/json" \
  -d '{"mensaje": "¿Cuántos días tengo para devolver algo?"}'
```

**Paso 2 · Imagen (25 min).** `projects/03-support-agent/Dockerfile`:

```dockerfile
FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY agent ./agent
COPY mock_crm ./mock_crm
COPY mcp_docuchat ./mcp_docuchat
# Sin CMD fijo: cada servicio indica su comando en compose
```

Y `.dockerignore` con `.venv`, `.env`, `evals/results`, `tests` y `__pycache__`.

Crea en ECR un repositorio `support-agent` y sube la imagen con los *push commands* de la consola, como en la semana 17.

```bash
git add -A && git commit -m "Support agent: API de chat con aprobación e imagen Docker"
```

---

### Miércoles 2 · 1 h · System design 3: DocuChat para 10.000 usuarios

Crea `practice/system-design/03-rag-a-escala.md`. Esta vez el sistema es **tuyo**: usa tus números reales de latencia y coste.

```markdown
# Diseño: DocuChat para 10.000 usuarios activos

## 1. Supuestos
- 10.000 usuarios, 20 preguntas/día cada uno → preguntas por segundo de media y en pico (×5): ?
- 5 PDFs por usuario, 300 chunks cada uno → número de vectores: ?
- Mi coste actual por pregunta: X $ → coste mensual: ?

## 2. Cuellos de botella actuales
(Una EC2, sin caché, ingesta síncrona en la petición, límite en memoria…)

## 3. Cambios
| Problema | Solución | Por qué |
|---|---|---|
| Subir un PDF bloquea la petición | Ingesta asíncrona con cola + worker (como en la semana 29) | |
| Preguntas repetidas cuestan dinero | Caché de respuestas o de embeddings (Redis) | |
| Un solo servidor | Varias instancias detrás de un balanceador | |
| El limitador en memoria | Redis | |
| Búsqueda vectorial con millones de vectores | Índice HNSW bien ajustado, particionado por usuario o una base vectorial dedicada | |
| Calidad que se degrada sin avisar | Eval nocturno con el golden set + alertas | |

## 4. Diagrama
(cajas y flechas en texto)

## 5. Qué NO haría todavía y por qué
```

---

### Jueves 3 · 1 h · Servicios en el servidor

Entra por SSH al servidor (`cd ~/docuchat`).

**Paso 1 · Variables del agente (10 min).** Crea `.env.agente` (`chmod 600`). Fíjate en las URLs internas, que usan los nombres de los servicios:

```
GOOGLE_API_KEY=...
AGENT_DB_URI=postgresql://...supabase...        # la misma base de Supabase, SIN "+psycopg"
REDIS_URL=redis://redis:6379/0
CRM_URL=http://crm:8001
DOCUCHAT_URL=http://api:8000                    # DocuChat por la red interna
DOCUCHAT_API_KEY=la-clave-de-soporte
WEBHOOK_SECRET=...
WEBHOOK_URL=http://agent-api:8002/webhooks/ticket
SLACK_WEBHOOK_URL=...
API_KEYS={"tu-clave":"marco"}
CORS_ORIGINS=["https://tu-proyecto.vercel.app","http://localhost:5173"]
```

**Paso 2 · Servicios (20 min).** Añade a `compose.yml`, dentro de `services:` (cambia el registro por el tuyo):

```yaml
  agent-api:
    image: 123456789012.dkr.ecr.eu-south-2.amazonaws.com/support-agent:${AGENT_TAG:-latest}
    command: ["/app/.venv/bin/uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8002"]
    env_file: .env.agente
    restart: unless-stopped
    depends_on: [redis, crm]
  worker:
    image: 123456789012.dkr.ecr.eu-south-2.amazonaws.com/support-agent:${AGENT_TAG:-latest}
    command: ["/app/.venv/bin/python", "-m", "agent.worker"]
    env_file: .env.agente
    restart: unless-stopped
    depends_on: [redis]
  crm:
    image: 123456789012.dkr.ecr.eu-south-2.amazonaws.com/support-agent:${AGENT_TAG:-latest}
    command: ["/app/.venv/bin/uvicorn", "mock_crm.main:app", "--host", "0.0.0.0", "--port", "8001"]
    env_file: .env.agente
    restart: unless-stopped
  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

Ninguno tiene `ports:`: solo Caddy está expuesto a Internet.

**Paso 3 · Rutas en Caddy (10 min).** Sustituye el `Caddyfile`:

```
docuchat-marco.duckdns.org {
    handle_path /agent/* {
        reverse_proxy agent-api:8002
    }
    handle {
        reverse_proxy api:8000
    }
}
```

`handle_path` quita el prefijo `/agent` antes de pasar la petición: el agente recibe `/chat`, no `/agent/chat`.

**Paso 4 · Arrancar y probar (20 min):**

```bash
aws ecr get-login-password --region eu-south-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.eu-south-2.amazonaws.com
docker compose up -d
docker compose ps        # todos "running"
docker compose logs agent-api --tail 30
```

Desde tu Mac:

```bash
curl -s https://docuchat-marco.duckdns.org/agent/health
curl -s -X POST https://docuchat-marco.duckdns.org/agent/chat -H "X-API-Key: TU_CLAVE" \
  -H "Content-Type: application/json" -d '{"mensaje": "Hola"}'
```

**Está bien si** el primero da `{"status":"ok"}` y el segundo, un saludo diciendo que es un asistente virtual.

---

### Sábado 5 · 1,5 h

**Técnico, 30 min · Pantalla de demo con aprobación.** En el frontend de DocuChat, crea `src/components/SoporteDemo.tsx`:

```tsx
import { useState } from "react";
import { API_URL } from "../api/client";

type Turno = { quien: "cliente" | "agente" | "sistema"; texto: string };
type Respuesta = { hilo: string; respuesta: string | null; aprobacion_pendiente: Record<string, unknown> | null };

export default function SoporteDemo({ apiKey }: { apiKey: string }) {
  const [hilo, setHilo] = useState<string | null>(null);
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [texto, setTexto] = useState("");
  const [pendiente, setPendiente] = useState<Record<string, unknown> | null>(null);
  const [cargando, setCargando] = useState(false);

  async function llamar(ruta: string, cuerpo: object) {
    setCargando(true);
    const r = await fetch(`${API_URL}/agent${ruta}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": apiKey },
      body: JSON.stringify(cuerpo),
    });
    const datos: Respuesta = await r.json();
    setCargando(false);
    setHilo(datos.hilo);
    setPendiente(datos.aprobacion_pendiente);
    if (datos.respuesta) setTurnos((t) => [...t, { quien: "agente", texto: datos.respuesta! }]);
    if (datos.aprobacion_pendiente) {
      setTurnos((t) => [...t, { quien: "sistema", texto: `El agente pide aprobación: ${JSON.stringify(datos.aprobacion_pendiente)}` }]);
    }
  }

  async function enviar() {
    if (!texto.trim()) return;
    setTurnos((t) => [...t, { quien: "cliente", texto }]);
    setTexto("");
    await llamar("/chat", { mensaje: texto, hilo });
  }

  return (
    <section className="tarjeta">
      <h2>Agente de soporte (demo)</h2>
      <p className="muted">Tienda ficticia TechStore. Prueba con un email de cliente del CRM simulado.</p>
      {turnos.map((t, i) => (
        <p key={i} className={t.quien === "sistema" ? "aviso" : ""}>
          <strong>{t.quien}:</strong> {t.texto}
        </p>
      ))}
      {pendiente && (
        <div className="fuente">
          <p>Como supervisor, ¿apruebas esta acción?</p>
          <button disabled={cargando} onClick={() => llamar(`/chat/${hilo}/decision`, { aprobar: true })}>Aprobar</button>{" "}
          <button disabled={cargando} onClick={() => llamar(`/chat/${hilo}/decision`, { aprobar: false })}>Rechazar</button>
        </div>
      )}
      <form onSubmit={(e) => { e.preventDefault(); enviar(); }}>
        <input value={texto} onChange={(e) => setTexto(e.target.value)} disabled={cargando || !!pendiente}
               placeholder="Escribe como si fueras un cliente…" />
        <button type="submit" disabled={cargando || !!pendiente}>Enviar</button>
      </form>
    </section>
  );
}
```

En `App.tsx`, añade dos botones arriba ("DocuChat" y "Agente de soporte") que cambien un estado `vista` y muestren el chat de DocuChat o `<SoporteDemo apiKey={apiKey} />`. Haz push: Vercel lo publica solo.

**Prueba:** cliente con pedido retrasado → ticket. Luego "cierra el ticket" → aparecen los botones → Rechazar → el agente lo explica.

**Carrera, 1 h · 2 candidaturas**, ya con las dos demos en vivo.

> **CI/CD del agente:** si te sobra tiempo, copia `docuchat-deploy.yml` como `agent-deploy.yml`, cambiando la carpeta, el repositorio de ECR (`support-agent`), la variable (`AGENT_TAG`) y los servicios (`agent-api worker crm`). Si no, hazlo en la semana 34, que es más ligera.

---

### Domingo 6 · 15 min · Checkpoint

1. **Checkpoint:** fin de S32 en la tabla del roadmap: MCP, integraciones, guardrails, evals y despliegue; 46 problemas, 33 candidaturas y 13 contactos.
2. Sección **Deployment** en el README del proyecto 03 con la URL de la demo y el diagrama de servicios.
3. Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] API de chat con aprobación por endpoint
- [ ] Una imagen y tres servicios (API, worker, CRM) en el servidor
- [ ] CRM y Redis sin exponer; `/agent/*` detrás de Caddy
- [ ] Pantalla de demo con botones de aprobación en Vercel
- [ ] System design de RAG a escala
- [ ] 2 candidaturas

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `agent-api` se reinicia sin parar | `docker compose logs agent-api`. Lo habitual: `AGENT_DB_URI` con `+psycopg` (aquí va sin él) o el MCP no arranca porque falta `DOCUCHAT_API_KEY`. |
| `/agent/chat` da 404 | Falta `handle_path` en Caddy o no reiniciaste Caddy (`docker compose restart caddy`). |
| El servidor va muy lento o mata procesos | Falta de memoria: confirma que es una t3.small (`free -h`). |
| CORS en la demo | Añade la URL de Vercel a `CORS_ORIGINS` de `.env.agente` y reinicia `agent-api`. |
| El webhook no llega al worker en el servidor | `WEBHOOK_URL` debe apuntar a `http://agent-api:8002/...`, no a `localhost`. |
