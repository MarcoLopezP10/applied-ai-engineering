# Semana 24 · 5–11 abr · Agentes desde cero

[← Semana 23](semana-23.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 25 →](semana-25.md)

🎯 **Objetivo:** entender de verdad qué es un agente construyendo uno **sin frameworks**: un bucle en el que el modelo decide qué herramienta usar, observa el resultado y vuelve a decidir, hasta resolver una tarea de varios pasos. Empieza el term 3 y la ola 3 de candidaturas está en su punto más alto.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 6 | 1 h | Técnico | Lectura sobre agentes + herramientas seguras |
| Miércoles 7 | 1 h | Algoritmos | Clone Graph y Max Area of Island |
| Jueves 8 | 1 h | Técnico | El bucle del agente con registro de pasos (lo escribes tú) |
| Sábado 10 | 1,5 h | Técnico + carrera | Tareas de varios pasos (30 min) + 2 candidaturas y métrica del capstone (1 h) |
| Domingo 11 | 15 min | Cierre | Log y PR |

Material de apoyo: roadmap técnico, semana 24.

---

### 📖 Qué vas a aprender

**Agente = LLM + herramientas + bucle.** La diferencia con tu CLI de la semana 6 es de grado: allí el modelo usaba como mucho una herramienta para responder. Un agente encadena varias para resolver una tarea que **no sabe de antemano cómo resolver**:

```
Tarea: "¿Qué día será dentro de 100 días? Y si trabajo 7,5 h diarias, ¿cuántas horas son?"
  paso 1 → fecha_dentro_de(100)   → "viernes 16/07/2027"
  paso 2 → calcular("100*7.5")     → "750.0"
  paso 3 → respuesta final usando las dos observaciones
```

**Workflow o agente.** Si los pasos son siempre los mismos (buscar → responder, como DocuChat), es un **workflow**: más barato, más rápido y más predecible. Un agente solo compensa cuando los pasos dependen de lo que va encontrando. Saber decir "aquí no hace falta un agente" es una señal de madurez muy valorada en entrevistas.

**Los tres riesgos de un agente:**

- **Bucles infinitos** → límite de pasos.
- **Herramientas peligrosas** → nunca `eval()`, y validar los argumentos.
- **Errores opacos** → registrar cada paso: qué pidió, con qué argumentos y qué obtuvo.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana24-agente-basico
mkdir -p practice/semana24
```

---

### Martes 6 · 1 h · Lectura y herramientas

**Paso 1 · Lectura (30 min).** Lee *Building effective agents* de Anthropic (búscalo por el título; está en su web de ingeniería). Responde en `practice/semana24/NOTAS.md` con tus palabras:

1. ¿Qué diferencia un *workflow* de un agente?
2. Nombra 3 patrones de workflow de los que describe.
3. ¿Cuándo recomienda **no** usar un agente?

**Paso 2 · Herramientas (30 min).** Crea `practice/semana24/herramientas.py`. Fíjate en `calcular`: evalúa matemáticas **sin `eval()`**, porque `eval` ejecutaría cualquier código que el modelo le pasara.

~~~python
"""Herramientas del agente básico."""
import ast
import json
import operator as op
from datetime import date, timedelta

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
OPERADORES = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
              ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg}


def _evaluar(nodo):
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in OPERADORES:
        return OPERADORES[type(nodo.op)](_evaluar(nodo.left), _evaluar(nodo.right))
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in OPERADORES:
        return OPERADORES[type(nodo.op)](_evaluar(nodo.operand))
    raise ValueError("Solo se permiten números y + - * / **")


def calcular(expresion: str) -> str:
    return str(_evaluar(ast.parse(expresion, mode="eval").body))


def fecha_dentro_de(dias: int) -> str:
    d = date.today() + timedelta(days=dias)
    return f"{DIAS[d.weekday()]} {d:%d/%m/%Y}"


def tiempo(ciudad: str) -> str:
    """Datos de juguete: en un caso real llamaría a una API del tiempo."""
    datos = {"madrid": "soleado, 22 °C", "lisboa": "nublado, 18 °C", "londres": "lluvia, 12 °C"}
    return datos.get(ciudad.lower(), f"No tengo datos de {ciudad}")


FUNCIONES = {"calcular": calcular, "fecha_dentro_de": fecha_dentro_de, "tiempo": tiempo}

TOOLS = [
    {"type": "function", "function": {
        "name": "calcular", "description": "Calcula una expresión aritmética, por ejemplo '100*7.5'.",
        "parameters": {"type": "object", "properties": {"expresion": {"type": "string"}}, "required": ["expresion"]}}},
    {"type": "function", "function": {
        "name": "fecha_dentro_de", "description": "Fecha y día de la semana dentro de N días desde hoy.",
        "parameters": {"type": "object", "properties": {"dias": {"type": "integer"}}, "required": ["dias"]}}},
    {"type": "function", "function": {
        "name": "tiempo", "description": "Tiempo actual en una ciudad.",
        "parameters": {"type": "object", "properties": {"ciudad": {"type": "string"}}, "required": ["ciudad"]}}},
]


def ejecutar(nombre: str, argumentos_json: str) -> str:
    try:
        return FUNCIONES[nombre](**json.loads(argumentos_json or "{}"))
    except Exception as error:
        return f"Error en {nombre}: {error}"
~~~

Pruébalo:

```bash
uv run python -c "
import sys; sys.path.insert(0, 'practice/semana24')
from herramientas import calcular
print(calcular('2**10 - 24'))
print(calcular('__import__(\"os\").system(\"ls\")'))"
```

**Está bien si** la primera da `1000` y la segunda lanza `ValueError` en lugar de ejecutar `ls`.

---

### Miércoles 7 · 1 h · Algoritmos (Graphs)

**Clone Graph** (Medium) → `practice/algoritmos/clone_graph.py`

~~~python
class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors or []


def clone_graph(node):
    ...


if __name__ == "__main__":
    a, b, c, d = Node(1), Node(2), Node(3), Node(4)
    a.neighbors, b.neighbors, c.neighbors, d.neighbors = [b, d], [a, c], [b, d], [a, c]
    copia = clone_graph(a)
    assert copia is not a and copia.val == 1
    assert sorted(n.val for n in copia.neighbors) == [2, 4]
    assert copia.neighbors[0] is not b  # son copias, no los originales
    print("OK")
~~~

<details>
<summary>Pista</summary>
Un diccionario {nodo original → copia}. Recorre con DFS: si el nodo ya está en el diccionario, devuelve su copia; si no, crea la copia, guárdala y copia sus vecinos.
</details>

**Max Area of Island** (Medium) → `practice/algoritmos/max_area_island.py`

~~~python
def max_area_of_island(grid: list[list[int]]) -> int:
    ...


if __name__ == "__main__":
    grid = [[0, 0, 1, 0], [1, 1, 1, 0], [0, 0, 0, 0], [0, 1, 1, 0]]
    assert max_area_of_island(grid) == 4
    print("OK")
~~~

<details>
<summary>Pista</summary>
Como Number of Islands, pero la función que "hunde" la isla devuelve cuántas celdas ha hundido.
</details>

---

### Jueves 8 · 1 h · El bucle del agente (lo escribes tú)

Crea `practice/semana24/agente_basico.py`:

~~~python
"""Agente sin frameworks: decide → actúa → observa → repite."""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from herramientas import TOOLS, ejecutar

load_dotenv()
client = OpenAI(api_key=os.getenv("GOOGLE_API_KEY"),
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
MODELO = "gemini-3.8-flash"
MAX_PASOS = 5
SYSTEM = ("Eres un agente que resuelve tareas paso a paso usando herramientas. "
          "Usa una herramienta cada vez que necesites un dato o un cálculo; no calcules de cabeza.")


def ejecutar_agente(tarea: str) -> str:
    mensajes = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": tarea}]
    # TODO:
    # Repite hasta MAX_PASOS veces:
    #   1. Llama al modelo con mensajes y tools=TOOLS
    #   2. Si no pide herramientas → imprime "✓ respuesta final" y devuelve el texto
    #   3. Si pide herramientas → añade su mensaje (con tool_calls) al historial y, para cada llamada:
    #        - imprime: f"paso {paso}: {nombre}({argumentos})"
    #        - resultado = ejecutar(nombre, argumentos)
    #        - imprime: f"   → {resultado}"
    #        - añade el mensaje role "tool" con el resultado y su tool_call_id
    # Si se agotan los pasos → devuelve "No he podido terminar en MAX_PASOS pasos"
    raise NotImplementedError


if __name__ == "__main__":
    print(ejecutar_agente(" ".join(sys.argv[1:]) or "¿Qué tiempo hace en Lisboa?"))
~~~

<details>
<summary>Solución</summary>

~~~python
def ejecutar_agente(tarea: str) -> str:
    mensajes = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": tarea}]
    for paso in range(1, MAX_PASOS + 1):
        mensaje = client.chat.completions.create(model=MODELO, messages=mensajes, tools=TOOLS).choices[0].message
        if not mensaje.tool_calls:
            print("✓ respuesta final")
            return mensaje.content
        mensajes.append({"role": "assistant", "content": mensaje.content,
                         "tool_calls": [t.model_dump() for t in mensaje.tool_calls]})
        for llamada in mensaje.tool_calls:
            nombre, argumentos = llamada.function.name, llamada.function.arguments
            print(f"paso {paso}: {nombre}({argumentos})")
            resultado = ejecutar(nombre, argumentos)
            print(f"   → {resultado}")
            mensajes.append({"role": "tool", "tool_call_id": llamada.id, "content": resultado})
    return f"No he podido terminar en {MAX_PASOS} pasos"
~~~
</details>

```bash
cd practice/semana24
uv run python agente_basico.py "¿Qué tiempo hace en Lisboa?"
```

---

### Sábado 10 · 1,5 h

**Técnico, 30 min · Tareas de varios pasos.** Ejecuta estas 4 y, para cada una, copia el registro de pasos en `NOTAS.md`:

1. "¿Qué día será dentro de 100 días? Si trabajo 7,5 h al día todos esos días, ¿cuántas horas son?"
2. "¿En qué ciudad hace más calor ahora, Madrid, Lisboa o Londres? ¿Cuántos grados de diferencia hay con la más fría?"
3. "¿Cuánto es 15 % de 2.340?" (¿Usa la herramienta o calcula de cabeza?)
4. Una que fuerce el límite: "Calcula 1+1, luego súmale 1 al resultado, y repite hasta llegar a 10, una operación cada vez."

Responde: ¿qué tarea habría resuelto mejor un *workflow* fijo? ¿Qué pasó con el límite de pasos?

**Carrera, 1 h:**

1. **2 candidaturas de la ola 3** (40 min).
2. **Capstone (20 min).** Si ya conoces la empresa, propón a tu equipo **qué métrica de impacto** vais a medir desde el primer día (horas ahorradas, errores evitados, tiempo de respuesta…) y cómo vais a medir la situación de partida. Sin esa medida inicial, no habrá cifra que contar en las entrevistas.

---

### Domingo 11 · 15 min · Cierre

1. Log semanal. Empieza la concentración Advanced AI: apunta las horas reales de esta semana para ver si el term 3 te da las mismas 4–5 h.
2. PR y merge.

---

✅ **Checklist**
- [ ] Sé explicar el bucle de un agente y cuándo NO usar uno
- [ ] `calcular` no ejecuta código arbitrario
- [ ] Límite de pasos y registro de cada paso funcionando
- [ ] 4 tareas probadas y analizadas en `NOTAS.md`
- [ ] 2 problemas de grafos
- [ ] 2 candidaturas y métrica del capstone propuesta

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: herramientas` | Ejecuta el agente desde dentro de `practice/semana24`. |
| El modelo calcula de cabeza en vez de usar la herramienta | Refuerza el system prompt: "Para cualquier cálculo usa SIEMPRE la herramienta calcular". |
| Llama a la misma herramienta en bucle | Mira si el resultado es un error que no entiende. Haz que los mensajes de error digan qué debe cambiar. |
