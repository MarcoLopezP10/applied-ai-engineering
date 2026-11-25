# Semana 28 · 3–9 may · MCP: DocuChat como herramienta

[← Semana 27](semana-27.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 29 →](semana-29.md)

🎯 **Objetivo:** conectar tus dos proyectos con el estándar que más está creciendo en las ofertas: un **servidor MCP** que expone la búsqueda de DocuChat como herramienta. Lo usarán tu agente de soporte (para responder sobre políticas de TechStore) y cualquier cliente MCP, como Claude Code. Además, tu primer ejercicio de system design.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 4 | 1 h | Técnico | Base de conocimiento de TechStore + servidor MCP |
| Miércoles 5 | 1 h | System design | Acortador de URLs |
| Jueves 6 | 1 h | Técnico | El agente usa el servidor MCP |
| Sábado 8 | 1,5 h | Técnico + carrera | Probarlo desde Claude Code (30 min) + 2 candidaturas (1 h) |
| Domingo 9 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**MCP (Model Context Protocol).** Un estándar abierto para que cualquier aplicación con IA (Claude, IDEs o tus propios agentes) use herramientas y datos externos de la misma forma. Escribes el servidor **una vez** y lo usan todos los clientes. Antes, cada integración se hacía a mano para cada aplicación.

```
Claude Code ──┐
Claude Desktop├──MCP──▶ servidor "docuchat" ──HTTP──▶ API de DocuChat (/search)
Tu agente ────┘          (herramienta buscar_en_documentos)
```

**Transporte stdio.** El cliente arranca el servidor como un proceso y hablan por su entrada y salida estándar. Es lo más sencillo para empezar; para servidores remotos existe HTTP.

**Por qué el servidor llama a la API y no a la base de datos.** Así respeta la autenticación, los límites y los logs de DocuChat. Un FDE nunca se salta las APIs del cliente para ir directo a su base de datos.

**System design.** En las entrevistas de SWE y AI Engineer te dan un problema abierto ("diseña un acortador de URLs") y 45 minutos. No buscan la respuesta perfecta: buscan que aclares requisitos, estimes tamaños, propongas componentes y razones las alternativas.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana28-mcp
cd projects/03-support-agent
uv add "mcp[cli]" langchain-mcp-adapters
```

---

### Martes 4 · 1 h · Base de conocimiento y servidor MCP

**Paso 1 · Las políticas de TechStore (20 min).** Escribe en Google Docs o Pages un documento de una página llamado "Políticas de TechStore" y expórtalo como PDF. Inventa datos concretos:

- **Envíos:** 2–5 días laborables (premium: 24–48 h). Se considera retrasado a partir del día 7.
- **Devoluciones:** 30 días desde la entrega, producto en su caja; el cliente paga el envío salvo defecto.
- **Garantía:** 2 años; los portátiles, 3 años para premium.
- **Reembolsos:** 5–7 días laborables desde que llega la devolución.
- **Productos dañados en el envío:** foto en 48 h y reposición sin coste.

**Paso 2 · Subirlo a DocuChat (10 min).** En el `.env` del servidor de DocuChat, añade un usuario `soporte` a `API_KEYS` con una clave nueva y reinicia. Entra en la web con esa clave y sube el PDF. Guarda la clave en el `.env` de la raíz del repo:

```
DOCUCHAT_URL=https://docuchat-marco.duckdns.org
DOCUCHAT_API_KEY=la-clave-de-soporte
```

**Paso 3 · El servidor MCP (20 min).** Crea `mcp_docuchat/server.py`:

~~~python
"""Servidor MCP que expone la búsqueda de DocuChat como herramienta."""
import os

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
DOCUCHAT_URL = os.getenv("DOCUCHAT_URL", "http://localhost:8000")
DOCUCHAT_API_KEY = os.environ["DOCUCHAT_API_KEY"]

mcp = FastMCP("docuchat")


@mcp.tool()
def buscar_en_documentos(pregunta: str, k: int = 3) -> str:
    """Busca en la base de conocimiento de TechStore (envíos, devoluciones, garantía, reembolsos)
    y devuelve los fragmentos más relevantes con su documento y página."""
    r = httpx.get(
        f"{DOCUCHAT_URL}/search",
        params={"q": pregunta, "k": k},
        headers={"X-API-Key": DOCUCHAT_API_KEY},
        timeout=30,
    )
    if r.status_code != 200:
        return f"Error {r.status_code} al consultar DocuChat"
    return "\n\n".join(f"[{f['document']}, pág. {f['page']}] {f['text']}" for f in r.json())


if __name__ == "__main__":
    mcp.run()  # transporte stdio
~~~

**Paso 4 · Probarlo con el inspector (10 min):**

```bash
uv run mcp dev mcp_docuchat/server.py
```

Se abre el **MCP Inspector** en el navegador: Connect → Tools → `buscar_en_documentos` → pregunta "¿cuántos días tengo para devolver un producto?".

**Está bien si** devuelve el fragmento de tu PDF con "30 días".

```bash
git add -A && git commit -m "Support agent: servidor MCP de DocuChat"
```

---

### Miércoles 5 · 1 h · System design 1: acortador de URLs

Crea `practice/system-design/01-acortador-urls.md` y complétalo **antes** de leer la solución del [System Design Primer](https://github.com/donnemartin/system-design-primer) (busca "Pastebin" o "URL shortener"):

```markdown
# Diseño: acortador de URLs (tipo bit.ly)

## 1. Requisitos (5 min)
- Funcionales: crear URL corta, redirigir, (¿caducidad? ¿estadísticas?)
- No funcionales: latencia de la redirección, disponibilidad, escala

## 2. Estimaciones (5 min)
- URLs nuevas al día: 1 millón → por segundo: ?
- Lecturas por escritura: 100:1 → lecturas por segundo: ?
- Espacio en 5 años: ? (bytes por URL × URLs)

## 3. API (5 min)
- POST /urls {url} → {codigo}
- GET /{codigo} → 301/302 a la URL larga

## 4. Modelo de datos (5 min)
tabla urls(codigo PK, url_larga, creada, caduca, usuario)

## 5. Generar el código (10 min)
- Opción A: hash (MD5) de la URL y quedarse con 7 caracteres. Problema:
- Opción B: contador + base62. Problema:
- Elijo … porque …

## 6. Arquitectura (10 min)
cliente → balanceador → servicio → caché (Redis) → base de datos
¿Dónde está el cuello de botella? ¿Qué va en caché?

## 7. Qué mejoraría con más tiempo
```

Luego lee la solución y añade al final 3 cosas que no se te ocurrieron.

---

### Jueves 6 · 1 h · El agente usa el servidor MCP

Las herramientas de MCP son asíncronas, así que el agente pasa a funcionar con `async`.

**Paso 1 · Grafo con herramientas extra (15 min).** En `agent/graph.py`, sustituye desde `llm = ...` hasta el final por:

~~~python
llm = ChatOpenAI(
    model=os.getenv("CHAT_MODEL", "gemini-3.8-flash"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0,
)


def construir_grafo(tools_extra=(), **compile_kwargs):
    herramientas = TOOLS + list(tools_extra)
    llm_tools = llm.bind_tools(herramientas)

    async def agente(state: MessagesState) -> dict:
        mensajes = [{"role": "system", "content": SYSTEM}] + state["messages"]
        return {"messages": [await llm_tools.ainvoke(mensajes)]}

    grafo = StateGraph(MessagesState)
    grafo.add_node("agente", agente)
    grafo.add_node("tools", ToolNode(herramientas))
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition)
    grafo.add_edge("tools", "agente")
    return grafo.compile(**compile_kwargs)
~~~

Y añade al `SYSTEM` la regla:

```
8. Para preguntas sobre políticas (envíos, devoluciones, garantía, reembolsos), usa buscar_en_documentos
   y menciona el documento y la página. Si no aparece, di que no lo sabes.
```

**Paso 2 · Chat asíncrono con MCP (35 min).** Sustituye `agent/chat.py`:

~~~python
"""Chat de terminal: memoria, aprobación humana y herramientas MCP."""
import asyncio
import os
import sys
import uuid

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command

from agent.graph import construir_grafo

load_dotenv()
DB_URI = os.getenv("AGENT_DB_URI", "postgresql://agente:agente@localhost:5434/agente")

MCP_SERVIDORES = {
    "docuchat": {
        "command": sys.executable,  # el mismo Python del proyecto (vale en local y en Docker)
        "args": ["mcp_docuchat/server.py"],
        "transport": "stdio",
        "env": {k: os.environ[k] for k in ("PATH", "DOCUCHAT_URL", "DOCUCHAT_API_KEY")},
    }
}


async def main() -> None:
    hilo = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())[:8]
    tools_mcp = await MultiServerMCPClient(MCP_SERVIDORES).get_tools()
    print(f"Soporte TechStore · hilo {hilo} · herramientas MCP: {[t.name for t in tools_mcp]}\n")
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        app = construir_grafo(tools_extra=tools_mcp, checkpointer=checkpointer)
        config = {"configurable": {"thread_id": hilo}, "recursion_limit": 15}
        while (texto := (await asyncio.to_thread(input, "Cliente: ")).strip()).lower() != "exit":
            resultado = await app.ainvoke({"messages": [("user", texto)]}, config)
            while "__interrupt__" in resultado:
                print(f"\n⚠️  Supervisor: el agente quiere {resultado['__interrupt__'][0].value}")
                decision = (await asyncio.to_thread(input, "¿Apruebas? (si/no): ")).strip().lower()
                resultado = await app.ainvoke(Command(resume=decision), config)
            print(f"Agente: {resultado['messages'][-1].content}\n")


if __name__ == "__main__":
    asyncio.run(main())
~~~

Prueba (con el CRM arrancado): "¿cuántos días tengo para devolver un producto?" y luego "soy [email], mi pedido llegó roto, ¿qué hago?".

**Está bien si** en la primera usa `buscar_en_documentos` y menciona la página, y en la segunda combina las políticas (foto en 48 h) con un ticket en el CRM. Esa combinación es lo que hace a un agente útil para una empresa.

La conversación 5 de la semana 26 (política de devoluciones) ahora debería salir bien.

```bash
git add -A && git commit -m "Support agent: herramientas MCP de DocuChat en el agente"
```

---

### Sábado 8 · 1,5 h

**Técnico, 30 min · El mismo servidor en Claude Code.** Desde la raíz del repo, regístralo (cambia la ruta y la clave):

```bash
claude mcp add docuchat \
  -e DOCUCHAT_URL=https://docuchat-marco.duckdns.org \
  -e DOCUCHAT_API_KEY=la-clave-de-soporte \
  -- uv --directory ~/Projects/applied-ai-engineering/projects/03-support-agent run python mcp_docuchat/server.py
```

Abre Claude Code y pregúntale: "Usa la herramienta de docuchat para decirme la política de garantía de TechStore". **Está bien si** llama a `buscar_en_documentos`.

Añade al README del proyecto 03 una sección **MCP** con el diagrama de arriba y cómo registrarlo en un cliente. Es una buena frase para entrevistas: "el mismo servidor lo usan mi agente y Claude Code sin cambiar una línea".

**Carrera, 1 h · 2 candidaturas.**

---

### Domingo 9 · 15 min · Cierre

Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] PDF de políticas en DocuChat con un usuario propio
- [ ] Servidor MCP probado con el inspector
- [ ] El agente usa `buscar_en_documentos` y cita la página
- [ ] El mismo servidor funciona en Claude Code
- [ ] Ejercicio de system design hecho y comparado con la solución
- [ ] 2 candidaturas

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| El inspector no arranca | Necesita Node (lo instalaste en la semana 19) y `mcp[cli]`. |
| `KeyError: DOCUCHAT_API_KEY` | Falta en el `.env` de la raíz del repo, o no se cargó: comprueba el `load_dotenv()`. |
| `get_tools()` se queda colgado | El servidor falla al arrancar. Ejecuta `uv run python mcp_docuchat/server.py` a mano y mira el error. |
| `AsyncPostgresSaver` no existe | Actualiza `langgraph-checkpoint-postgres`. |
| La API de `langchain-mcp-adapters` es distinta | Cambia a menudo: busca "MultiServerMCPClient" en su README de GitHub. |
