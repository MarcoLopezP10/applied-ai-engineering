# Semana 26 · 19–25 abr · El caso: un agente de soporte contra un CRM

[← Semana 25](semana-25.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 27 →](semana-27.md)

🎯 **Objetivo:** tu segundo proyecto estrella arranca con un problema realista de **Forward Deployed Engineer**: una tienda ficticia (TechStore) quiere un agente que atienda a sus clientes consultando y modificando **su CRM**. Esta semana montas un CRM simulado y un agente que lo usa.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 20 | 1 h | Técnico | Proyecto y CRM simulado |
| Miércoles 21 | 1 h | Algoritmos | Climbing Stairs y House Robber |
| Jueves 22 | 1 h | Técnico | Herramientas del agente (una la escribes tú) y chat |
| Sábado 24 | 1,5 h | Técnico + carrera | 10 conversaciones de prueba (30 min) + candidatura y entrevista simulada (1 h) |
| Domingo 25 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**El trabajo de un FDE en pequeño.** El cliente tiene sistemas propios (aquí, un CRM con clientes, pedidos y tickets) y reglas de negocio ("primero identifica al cliente", "los premium tienen prioridad"). Tu agente tiene que trabajar **con sus sistemas y sus reglas**, no al revés.

**Simular el sistema del cliente.** No tienes acceso a un CRM real, así que lo simulas con una API y datos falsos pero realistas (`Faker`) y **con semilla fija**: los datos son siempre los mismos, lo que te permitirá evaluar el agente en la semana 31.

**Reglas de negocio en el prompt.** El system prompt deja de ser "eres útil" y pasa a ser una especificación: qué puede hacer, en qué orden y qué no debe hacer nunca.

---

### Martes 20 · 1 h · Proyecto y CRM simulado

```bash
git checkout main && git pull
git checkout -b semana26-agente-soporte
mkdir -p projects/03-support-agent && cd projects/03-support-agent
uv init --app --name support-agent . && rm main.py
mkdir -p mock_crm agent tests scenarios docs
touch mock_crm/__init__.py agent/__init__.py
uv add fastapi "uvicorn[standard]" faker httpx langgraph langchain-openai python-dotenv
uv add --dev pytest
```

Añade al final de `pyproject.toml` estas líneas, para que los tests puedan importar el código del proyecto:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

Crea `mock_crm/main.py`. Es código de apoyo: léelo, pero no hace falta que lo escribas tú.

~~~python
"""CRM simulado de TechStore: clientes, pedidos y tickets con datos falsos y reproducibles."""
import random
from datetime import date, timedelta
from typing import Literal

from faker import Faker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

Faker.seed(42)
random.seed(42)  # misma semilla → mismos datos siempre (clave para evaluar)
fake = Faker("es_ES")

PRODUCTOS = ["Portátil Pro 14", "Auriculares X2", "Monitor 27 pulgadas", "Teclado mecánico", "Ratón inalámbrico"]
ESTADOS = ["preparando", "enviado", "entregado", "retrasado", "devuelto"]

CLIENTES = {
    i: {"id": i, "nombre": fake.name(), "email": fake.unique.email(), "plan": random.choice(["básico", "premium"])}
    for i in range(1, 51)
}
PEDIDOS = {
    i: {"id": i, "cliente_id": random.randint(1, 50), "producto": random.choice(PRODUCTOS),
        "estado": random.choice(ESTADOS),
        "fecha": str(date(2027, 3, 1) + timedelta(days=random.randint(0, 40)))}
    for i in range(1, 151)
}
TICKETS: dict[int, dict] = {}


class TicketIn(BaseModel):
    cliente_id: int
    asunto: str
    prioridad: Literal["baja", "media", "alta"]
    pedido_id: int | None = None


class TicketUpdate(BaseModel):
    estado: Literal["abierto", "en_curso", "resuelto"]
    comentario: str | None = None


app = FastAPI(title="CRM simulado de TechStore")


def _cliente(cliente_id: int) -> dict:
    if cliente_id not in CLIENTES:
        raise HTTPException(404, f"No existe el cliente {cliente_id}")
    return CLIENTES[cliente_id]


@app.get("/clientes")
def buscar_cliente(email: str):
    for c in CLIENTES.values():
        if c["email"].lower() == email.lower().strip():
            return c
    raise HTTPException(404, "No hay ningún cliente con ese email")


@app.get("/clientes/{cliente_id}/pedidos")
def pedidos_de_cliente(cliente_id: int):
    _cliente(cliente_id)
    return [p for p in PEDIDOS.values() if p["cliente_id"] == cliente_id]


@app.get("/pedidos/{pedido_id}")
def ver_pedido(pedido_id: int):
    if pedido_id not in PEDIDOS:
        raise HTTPException(404, f"No existe el pedido {pedido_id}")
    return PEDIDOS[pedido_id]


@app.get("/clientes/{cliente_id}/tickets")
def tickets_de_cliente(cliente_id: int):
    _cliente(cliente_id)
    return [t for t in TICKETS.values() if t["cliente_id"] == cliente_id]


@app.post("/tickets", status_code=201)
def crear_ticket(ticket: TicketIn):
    _cliente(ticket.cliente_id)
    nuevo = {"id": len(TICKETS) + 1, "estado": "abierto", "comentarios": [], **ticket.model_dump()}
    TICKETS[nuevo["id"]] = nuevo
    return nuevo


@app.patch("/tickets/{ticket_id}")
def actualizar_ticket(ticket_id: int, cambio: TicketUpdate):
    if ticket_id not in TICKETS:
        raise HTTPException(404, f"No existe el ticket {ticket_id}")
    TICKETS[ticket_id]["estado"] = cambio.estado
    if cambio.comentario:
        TICKETS[ticket_id]["comentarios"].append(cambio.comentario)
    return TICKETS[ticket_id]


@app.get("/debug/clientes")
def ejemplos(n: int = 5):
    """Solo para pruebas: unos cuantos clientes con sus pedidos."""
    return [{**c, "pedidos": pedidos_de_cliente(c["id"])} for c in list(CLIENTES.values())[:n]]
~~~

```bash
uv run uvicorn mock_crm.main:app --port 8001 --reload
```

Abre http://localhost:8001/debug/clientes y **apunta 3 clientes** en `docs/clientes_prueba.md`: uno premium con un pedido retrasado, uno básico con un pedido enviado y uno sin pedidos (si lo hay). Los usarás toda la semana.

```bash
git add -A && git commit -m "Support agent: proyecto y CRM simulado"
```

---

### Miércoles 21 · 1 h · Algoritmos (Programación dinámica 1-D)

**Programación dinámica:** si la solución de un problema se construye con las soluciones de problemas más pequeños que se repiten, guárdalas en vez de recalcularlas.

**Climbing Stairs** (Easy) → `practice/algoritmos/climbing_stairs.py`

~~~python
def climb_stairs(n: int) -> int:
    """Formas de subir n escalones subiendo 1 o 2 cada vez."""
    ...


if __name__ == "__main__":
    assert climb_stairs(2) == 2
    assert climb_stairs(3) == 3
    assert climb_stairs(10) == 89
    print("OK")
~~~

**House Robber** (Medium) → `practice/algoritmos/house_robber.py`

~~~python
def rob(nums: list[int]) -> int:
    """Máximo a robar sin robar dos casas seguidas."""
    ...


if __name__ == "__main__":
    assert rob([1, 2, 3, 1]) == 4
    assert rob([2, 7, 9, 3, 1]) == 12
    print("OK")
~~~

<details>
<summary>Pistas</summary>
Climbing Stairs: para llegar al escalón n vienes del n-1 o del n-2. House Robber: en cada casa, o la robas (y sumas lo mejor hasta dos casas antes) o no (y te quedas con lo mejor hasta la anterior).
</details>

---

### Jueves 22 · 1 h · Herramientas y chat

**Paso 1 · Herramientas (35 min).** Crea `agent/tools.py`. Hay cuatro hechas; `crear_ticket` la escribes tú:

~~~python
"""Herramientas del agente: cada una llama a una ruta del CRM."""
import json
import os

import httpx
from langchain_core.tools import tool

CRM_URL = os.getenv("CRM_URL", "http://localhost:8001")


def _llamar(metodo: str, ruta: str, **kwargs) -> str:
    """Llama al CRM y devuelve JSON como texto. Los errores también vuelven como texto."""
    try:
        r = httpx.request(metodo, f"{CRM_URL}{ruta}", timeout=10, **kwargs)
        if r.status_code >= 400:
            return f"Error {r.status_code}: {r.json().get('detail', r.text)}"
        return json.dumps(r.json(), ensure_ascii=False)
    except httpx.HTTPError as error:
        return f"Error de conexión con el CRM: {error}"


@tool
def buscar_cliente(email: str) -> str:
    """Busca un cliente por su email. Devuelve id, nombre, email y plan (básico o premium)."""
    return _llamar("GET", "/clientes", params={"email": email})


@tool
def ver_pedidos(cliente_id: int) -> str:
    """Lista los pedidos de un cliente con su producto, estado y fecha."""
    return _llamar("GET", f"/clientes/{cliente_id}/pedidos")


@tool
def ver_pedido(pedido_id: int) -> str:
    """Detalle de un pedido por su número."""
    return _llamar("GET", f"/pedidos/{pedido_id}")


# TODO: escribe la herramienta crear_ticket:
#   - argumentos: cliente_id (int), asunto (str), prioridad (str: "baja", "media" o "alta"),
#     pedido_id (int | None = None)
#   - docstring clara: cuándo usarla y qué significa cada prioridad
#   - llama a POST /tickets con json={...}


@tool
def actualizar_ticket(ticket_id: int, estado: str, comentario: str | None = None) -> str:
    """Cambia el estado de un ticket a 'abierto', 'en_curso' o 'resuelto', con un comentario opcional."""
    return _llamar("PATCH", f"/tickets/{ticket_id}", json={"estado": estado, "comentario": comentario})


TOOLS = [buscar_cliente, ver_pedidos, ver_pedido, crear_ticket, actualizar_ticket]
~~~

<details>
<summary>Solución de crear_ticket</summary>

~~~python
@tool
def crear_ticket(cliente_id: int, asunto: str, prioridad: str, pedido_id: int | None = None) -> str:
    """Crea un ticket de soporte para un cliente cuando hay una incidencia.
    prioridad: 'alta' si el cliente es premium o el pedido está retrasado; 'media' para otros problemas;
    'baja' para consultas sin incidencia."""
    return _llamar("POST", "/tickets", json={"cliente_id": cliente_id, "asunto": asunto,
                                             "prioridad": prioridad, "pedido_id": pedido_id})
~~~
</details>

**Paso 2 · Grafo y prompt (15 min).** Crea `agent/graph.py`. Es el mismo grafo de la semana 25, con un system prompt que contiene las reglas del negocio:

~~~python
"""Agente de soporte de TechStore."""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.tools import TOOLS

load_dotenv()

SYSTEM = """Eres el agente de soporte de TechStore. Ayudas a clientes con sus pedidos.
Reglas:
1. Antes de dar información de pedidos, identifica al cliente por su email con buscar_cliente.
2. Nunca inventes estados, fechas, plazos ni políticas. Si no lo sabes, dilo.
3. Si un pedido está retrasado o el cliente reporta un problema, crea un ticket.
   Prioridad: alta si el cliente es premium o el pedido está retrasado; media para otros problemas;
   baja para consultas.
4. Confirma al cliente el número de ticket creado.
5. Responde en español, en pocas frases y con amabilidad."""

llm = ChatOpenAI(
    model=os.getenv("CHAT_MODEL", "gemini-3.8-flash"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0,
).bind_tools(TOOLS)


def agente(state: MessagesState) -> dict:
    return {"messages": [llm.invoke([{"role": "system", "content": SYSTEM}] + state["messages"])]}


def construir_grafo(**compile_kwargs):
    grafo = StateGraph(MessagesState)
    grafo.add_node("agente", agente)
    grafo.add_node("tools", ToolNode(TOOLS))
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition)
    grafo.add_edge("tools", "agente")
    return grafo.compile(**compile_kwargs)
~~~

`**compile_kwargs` es para poder pasarle la memoria la semana que viene.

**Paso 3 · Chat de terminal (10 min).** `agent/chat.py`:

~~~python
"""Chat de terminal con el agente de soporte."""
from agent.graph import construir_grafo

app = construir_grafo()
historial = []
print("Soporte TechStore · escribe 'exit' para salir\n")
while (texto := input("Cliente: ").strip()).lower() != "exit":
    resultado = app.invoke({"messages": historial + [("user", texto)]}, {"recursion_limit": 15})
    historial = resultado["messages"]
    for m in resultado["messages"][-4:]:
        if getattr(m, "tool_calls", None):
            for t in m.tool_calls:
                print(f"   [herramienta] {t['name']}({t['args']})")
    print(f"Agente: {historial[-1].content}\n")
~~~

Con el CRM arrancado en otra terminal:

```bash
uv run python -m agent.chat
```

```bash
git add -A && git commit -m "Support agent: herramientas del CRM, grafo y chat"
```

---

### Sábado 24 · 1,5 h

**Técnico, 30 min · 10 conversaciones.** Crea `scenarios/conversaciones.md` con estas 10 situaciones. Usa los emails de `docs/clientes_prueba.md`. Ejecuta cada una (escribe `exit` y vuelve a entrar entre conversaciones) y anota el resultado:

| # | Lo que dice el cliente | Qué debería hacer el agente | ¿Lo hizo? | Notas |
|---|---|---|:---:|---|
| 1 | "¿Dónde está mi pedido?" (sin dar email) | Pedir el email antes de nada | | |
| 2 | Da su email y pregunta por sus pedidos | buscar_cliente → ver_pedidos → resumen | | |
| 3 | Cliente premium con pedido retrasado: "llevo días esperando" | Ticket con prioridad **alta** y decir el número | | |
| 4 | Cliente básico: "el teclado llegó roto" | Ticket con prioridad **media** | | |
| 5 | "¿Cuál es vuestra política de devoluciones?" | Decir que no lo sabe (aún no tiene esa información) | | |
| 6 | Email que no existe | Decir que no lo encuentra, sin inventar | | |
| 7 | Pregunta por el pedido de **otro** cliente | No darle información de pedidos ajenos | | |
| 8 | "Cierra mi ticket, ya está resuelto" | actualizar_ticket a "resuelto" | | |
| 9 | "Hola" | Saludar y pedir en qué puede ayudar, sin herramientas | | |
| 10 | Pedido número 9999 | Decir que no existe | | |

**Está bien si** resuelve al menos 7 de 10. Para cada fallo, escribe por qué crees que falló: prompt, descripción de la herramienta o el modelo. Es el germen de los evals de la semana 31.

**Carrera, 1 h:** 1 candidatura (30 min) y la entrevista simulada si la tienes reservada; si no, resérvala.

---

### Domingo 25 · 15 min · Cierre

1. README provisional del proyecto 03 con: el problema (TechStore), cómo arrancar el CRM y el chat, y la tabla de las 10 conversaciones.
2. Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] CRM simulado con datos reproducibles
- [ ] 5 herramientas, incluida `crear_ticket` escrita por ti
- [ ] Reglas de negocio en el system prompt
- [ ] 10 conversaciones probadas, al menos 7 bien
- [ ] 2 problemas de programación dinámica
- [ ] 1 candidatura y entrevista simulada

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `Error de conexión con el CRM` | El CRM no está arrancado en el puerto 8001. |
| El agente da información sin pedir el email | Refuerza la regla 1 y añade "si el cliente no ha dado su email, pídeselo y no uses ninguna otra herramienta". |
| Pone prioridad media a un premium | Comprueba que `buscar_cliente` devuelve el plan y que la docstring de `crear_ticket` explica las prioridades. |
| `ModuleNotFoundError: agent` | Ejecuta con `uv run python -m agent.chat` desde `projects/03-support-agent`. |
