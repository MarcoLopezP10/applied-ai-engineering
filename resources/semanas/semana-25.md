# Semana 25 · 12–18 abr · LangGraph

[← Semana 24](semana-24.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 26 →](semana-26.md)

🎯 **Objetivo:** rehacer el agente de la semana 24 con **LangGraph**, el framework de agentes que más piden tus ofertas, y entender qué te da frente al bucle hecho a mano: estado explícito, grafo visible, memoria y pausas para aprobar (las usarás en dos semanas).

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 13 | 1 h | Técnico | Conceptos de LangGraph + herramientas y modelo |
| Miércoles 14 | 1 h | Algoritmos | Course Schedule y Pacific Atlantic Water Flow |
| Jueves 15 | 1 h | Técnico | Construir el grafo (lo escribes tú) |
| Sábado 17 | 1,5 h | Técnico + carrera | Comparar con tu versión y dibujar el grafo (30 min) + 2 candidaturas (1 h) |
| Domingo 18 | 15 min | Cierre | Log y PR |

Material de apoyo: roadmap técnico, semana 25, y la documentación oficial de LangGraph ("Quickstart").

> LangGraph cambia a menudo. El código es para LangGraph 0.4 o superior. Si un import falla, busca el nombre en su documentación.

---

### 📖 Qué vas a aprender

**Un agente como grafo:**

```
        ┌──────────────┐  ¿pide herramientas?   ┌──────────┐
START ─▶│    agente    │──────── sí ───────────▶│  tools   │
        │ (llama al LLM)│◀─────────────────────── │(las ejecuta)│
        └──────┬───────┘                          └──────────┘
               │ no
               ▼
              END
```

- **Estado (`MessagesState`):** la lista de mensajes que se va pasando de nodo en nodo. En tu versión era la variable `mensajes`.
- **Nodos:** funciones que reciben el estado y devuelven qué cambiar. `agente` llama al LLM; `tools` ejecuta las herramientas (ya viene hecho: `ToolNode`).
- **Arista condicional (`tools_condition`):** decide si se va a `tools` o se termina. Es tu `if not mensaje.tool_calls` de la semana pasada.
- **`recursion_limit`:** tu `MAX_PASOS`.

**Qué ganas frente a tu bucle:** con 3 herramientas, poco. Con un agente real, mucho: memoria persistente con una línea (*checkpointer*), pausar para pedir aprobación humana (`interrupt`), retomar conversaciones, trazas por nodo y un diagrama del flujo que se genera solo. Por eso primero lo hiciste a mano: ahora sabes qué hace el framework por debajo.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana25-langgraph
uv add langgraph langchain-openai   # en la raíz del repo
mkdir -p practice/semana25
cp practice/semana24/herramientas.py practice/semana25/
```

---

### Martes 13 · 1 h · Herramientas y modelo en LangChain

Crea `practice/semana25/agente_langgraph.py` con la primera parte. Fíjate en que las herramientas ahora se definen con `@tool`: el **docstring** es la descripción que ve el modelo y los *type hints* son su esquema. Ya no escribes el JSON a mano.

~~~python
"""El agente de la semana 24, ahora con LangGraph."""
import os
import sys

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

import herramientas as h

load_dotenv()


@tool
def calcular(expresion: str) -> str:
    """Calcula una expresión aritmética, por ejemplo '100*7.5'."""
    return h.calcular(expresion)


@tool
def fecha_dentro_de(dias: int) -> str:
    """Fecha y día de la semana dentro de N días desde hoy."""
    return h.fecha_dentro_de(dias)


@tool
def tiempo(ciudad: str) -> str:
    """Tiempo actual en una ciudad."""
    return h.tiempo(ciudad)


TOOLS = [calcular, fecha_dentro_de, tiempo]

llm = ChatOpenAI(
    model="gemini-3.8-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0,
)
llm_con_tools = llm.bind_tools(TOOLS)  # el modelo ya "sabe" qué herramientas tiene

SYSTEM = ("Eres un agente que resuelve tareas paso a paso usando herramientas. "
          "Para cualquier dato o cálculo usa SIEMPRE una herramienta.")
~~~

Comprueba que el modelo funciona:

```bash
cd practice/semana25
uv run python -c "from agente_langgraph import llm_con_tools; print(llm_con_tools.invoke('¿Qué tiempo hace en Madrid?').tool_calls)"
```

**Está bien si** imprime una lista con una llamada a `tiempo` con `{'ciudad': 'Madrid'}`.

---

### Miércoles 14 · 1 h · Algoritmos (Graphs)

**Course Schedule** (Medium) → `practice/algoritmos/course_schedule.py`

~~~python
def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    ...


if __name__ == "__main__":
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    print("OK")
~~~

<details>
<summary>Pista</summary>
Es detectar si un grafo dirigido tiene ciclos. Con DFS, marca cada nodo como "visitando" o "terminado": si llegas a uno que está "visitando", hay ciclo.
</details>

**Pacific Atlantic Water Flow** (Medium) → `practice/algoritmos/pacific_atlantic.py`

~~~python
def pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:
    ...


if __name__ == "__main__":
    h = [[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]
    esperado = [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]
    assert sorted(pacific_atlantic(h)) == esperado
    print("OK")
~~~

<details>
<summary>Pista</summary>
Piensa al revés: desde cada océano, "sube" por las celdas de altura igual o mayor (DFS). La respuesta son las celdas alcanzables desde los dos océanos.
</details>

---

### Jueves 15 · 1 h · Construir el grafo (lo escribes tú)

Añade a `agente_langgraph.py`:

~~~python
def agente(state: MessagesState) -> dict:
    """Nodo que llama al LLM con todo el historial."""
    mensajes = [{"role": "system", "content": SYSTEM}] + state["messages"]
    return {"messages": [llm_con_tools.invoke(mensajes)]}


def construir_grafo():
    # TODO:
    # 1. grafo = StateGraph(MessagesState)
    # 2. añade el nodo "agente" (la función de arriba) y el nodo "tools" (ToolNode(TOOLS))
    # 3. arista de START a "agente"
    # 4. arista condicional desde "agente" con tools_condition (va a "tools" o termina)
    # 5. arista de "tools" de vuelta a "agente"
    # 6. return grafo.compile()
    raise NotImplementedError


app = construir_grafo()

if __name__ == "__main__":
    tarea = " ".join(sys.argv[1:]) or "¿Qué tiempo hace en Lisboa?"
    resultado = app.invoke({"messages": [("user", tarea)]}, {"recursion_limit": 12})
    for m in resultado["messages"]:
        m.pretty_print()  # imprime cada mensaje: el tuyo, las llamadas, los resultados y la respuesta
~~~

<details>
<summary>Solución</summary>

~~~python
def construir_grafo():
    grafo = StateGraph(MessagesState)
    grafo.add_node("agente", agente)
    grafo.add_node("tools", ToolNode(TOOLS))
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition)
    grafo.add_edge("tools", "agente")
    return grafo.compile()
~~~
</details>

```bash
uv run python agente_langgraph.py "¿Qué día será dentro de 100 días? Si trabajo 7,5 h al día, ¿cuántas horas son?"
```

**Está bien si** `pretty_print` muestra tu mensaje, las llamadas a `fecha_dentro_de` y `calcular`, sus resultados y la respuesta final.

`recursion_limit` cuenta pasos de nodo (cada vuelta agente → tools son 2). Prueba la tarea del bucle de la semana pasada con `{"recursion_limit": 6}` y mira el error que da.

---

### Sábado 17 · 1,5 h

**Técnico, 30 min · Comparar y dibujar.**

1. **Diagrama.** Añade al final de `agente_langgraph.py` y ejecútalo:

    ~~~python
    if "--grafo" in sys.argv:
        print(app.get_graph().draw_mermaid())
    ~~~

    Pega la salida en `practice/semana25/README.md` dentro de un bloque ```` ```mermaid ````. GitHub lo dibuja solo.
2. **Comparación** en el mismo README, una tabla con tu versión de la semana 24:

    | | Bucle propio (S24) | LangGraph (S25) |
    |---|---|---|
    | Líneas de código del agente | | |
    | Control del flujo | | |
    | Límite de pasos | | |
    | Facilidad para depurar | | |
    | Memoria / pausas / reanudar | | |

    Y una conclusión de 2 frases: ¿cuándo usarías cada uno?

**Carrera, 1 h · 2 candidaturas.** En las de AI Engineer, ya puedes poner LangGraph en skills.

---

### Domingo 18 · 15 min · Cierre

Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] Herramientas con `@tool` y modelo con `bind_tools`
- [ ] Grafo agente ⇄ tools con arista condicional
- [ ] Misma tarea de varios pasos resuelta que en la S24
- [ ] Diagrama mermaid y comparación en el README
- [ ] 2 problemas de grafos y 2 candidaturas

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `ImportError` en `langgraph.prebuilt` | Versión distinta: busca `ToolNode` y `tools_condition` en la documentación de tu versión. |
| `GraphRecursionError` | Has llegado a `recursion_limit`. Súbelo, o mira el bucle con `pretty_print`. |
| El modelo no llama a herramientas con `ChatOpenAI` | Comprueba que usas `llm_con_tools` (con `bind_tools`) en el nodo, no `llm`. |
| Error 400 sobre `tool_call_id` | Mezclaste mensajes en formato diccionario y objetos de LangChain. En el nodo, usa siempre `state["messages"]` tal cual. |
