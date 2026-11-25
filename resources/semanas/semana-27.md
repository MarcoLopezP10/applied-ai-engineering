# Semana 27 · 26 abr – 2 may · Memoria y aprobación humana

[← Semana 26](semana-26.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 28 →](semana-28.md)

🎯 **Objetivo:** que el agente **recuerde** (la conversación, aunque reinicies, y lo importante de cada cliente entre conversaciones) y que **no cambie datos sin permiso** de una persona. Las dos cosas las pide cualquier empresa antes de dejar a un agente hablar con sus clientes.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 27 | 1 h | Técnico | Memoria de conversación persistente (checkpointer en Postgres) |
| Miércoles 28 | 1 h | Algoritmos | Coin Change y Longest Increasing Subsequence |
| Jueves 29 | 1 h | Técnico | Memoria de cliente: notas en el CRM |
| Sábado 1 | 1,5 h | Técnico + carrera | Aprobación humana con `interrupt` (30 min) + 2 candidaturas (1 h) |
| Domingo 2 | 15 min | Cierre | Checkpoint de abril, log y PR |

Material de apoyo: roadmap técnico, semana 26.

---

### 📖 Qué vas a aprender

**Dos memorias distintas:**

| | Memoria de conversación | Memoria de cliente |
|---|---|---|
| Qué guarda | Todos los mensajes de **un hilo** | Lo importante de **todas** las conversaciones con un cliente |
| Dónde | Checkpointer de LangGraph (Postgres) | Notas en el CRM (el sistema del cliente) |
| Para qué | Retomar una conversación cortada | Que el agente sepa que "ya llamó dos veces por el mismo pedido" |

**Checkpointer.** LangGraph guarda el estado del grafo después de cada paso, asociado a un `thread_id`. Al volver a invocar con el mismo `thread_id`, continúa donde estaba. Con Postgres, sobrevive a reinicios.

**Human-in-the-loop con `interrupt`.** Dentro de una herramienta, `interrupt(...)` **pausa el grafo** y devuelve el control a tu código con una petición ("quiero poner el ticket 3 como resuelto"). Cuando una persona decide, se reanuda con `Command(resume=decisión)`. Para que el grafo pueda pausarse y seguir, necesita el checkpointer.

**Ojo:** al reanudar, la herramienta se ejecuta **desde el principio**. Por eso el `interrupt` va lo primero, antes de cualquier efecto (llamar al CRM).

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana27-memoria-aprobacion
cd projects/03-support-agent
uv add langgraph-checkpoint-postgres "psycopg[binary,pool]"
```

---

### Martes 27 · 1 h · Memoria de conversación

**Paso 1 · Postgres para el agente (10 min).** `projects/03-support-agent/docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: agente
      POSTGRES_PASSWORD: agente
      POSTGRES_DB: agente
    ports:
      - "5434:5432"
    volumes:
      - agente_data:/var/lib/postgresql/data
volumes:
  agente_data:
```

```bash
docker compose up -d
```

**Paso 2 · Chat con hilos (35 min).** Sustituye `agent/chat.py`:

~~~python
"""Chat de terminal con memoria persistente por hilo."""
import os
import sys
import uuid

from langgraph.checkpoint.postgres import PostgresSaver

from agent.graph import construir_grafo

DB_URI = os.getenv("AGENT_DB_URI", "postgresql://agente:agente@localhost:5434/agente")


def main() -> None:
    hilo = sys.argv[1] if len(sys.argv) > 1 else str(uuid.uuid4())[:8]
    print(f"Soporte TechStore · hilo {hilo} (para retomarlo: python -m agent.chat {hilo})\n")
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()  # crea sus tablas la primera vez
        app = construir_grafo(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": hilo}, "recursion_limit": 15}
        while (texto := input("Cliente: ").strip()).lower() != "exit":
            # Solo se manda el mensaje nuevo: el historial lo recupera el checkpointer
            resultado = app.invoke({"messages": [("user", texto)]}, config)
            print(f"Agente: {resultado['messages'][-1].content}\n")


if __name__ == "__main__":
    main()
~~~

**Prueba de memoria (15 min):**

1. `uv run python -m agent.chat` → di tu email (uno de `docs/clientes_prueba.md`) y pregunta por tus pedidos. Apunta el número de hilo y sal con `exit`.
2. **Para el CRM y vuelve a arrancarlo**, o incluso reinicia el ordenador.
3. `uv run python -m agent.chat <hilo>` → pregunta "¿y cuál era el más antiguo?".

**Está bien si** responde sin volver a pedirte el email.

```bash
git add -A && git commit -m "Support agent: memoria de conversación con checkpointer en Postgres"
```

---

### Miércoles 28 · 1 h · Algoritmos (Programación dinámica)

**Coin Change** (Medium) → `practice/algoritmos/coin_change.py`

~~~python
def coin_change(coins: list[int], amount: int) -> int:
    """Mínimo de monedas para sumar amount, o -1 si no se puede."""
    ...


if __name__ == "__main__":
    assert coin_change([1, 2, 5], 11) == 3
    assert coin_change([2], 3) == -1
    assert coin_change([1], 0) == 0
    print("OK")
~~~

<details>
<summary>Pista</summary>
dp[x] = mínimo de monedas para sumar x. dp[0] = 0. Para cada x y cada moneda c ≤ x: dp[x] = min(dp[x], dp[x - c] + 1).
</details>

**Longest Increasing Subsequence** (Medium) → `practice/algoritmos/lis.py`

~~~python
def length_of_lis(nums: list[int]) -> int:
    ...


if __name__ == "__main__":
    assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4
    assert length_of_lis([7, 7, 7]) == 1
    print("OK")
~~~

<details>
<summary>Pista</summary>
dp[i] = longitud de la subsecuencia creciente más larga que termina en i. Mira todos los j < i con nums[j] < nums[i]. Es O(n²) y vale.
</details>

---

### Jueves 29 · 1 h · Memoria de cliente

**Paso 1 · Notas en el CRM (10 min).** Añade a `mock_crm/main.py`:

~~~python
NOTAS: dict[int, list[dict]] = {}


class NotaIn(BaseModel):
    texto: str


@app.get("/clientes/{cliente_id}/notas")
def ver_notas(cliente_id: int):
    _cliente(cliente_id)
    return NOTAS.get(cliente_id, [])


@app.post("/clientes/{cliente_id}/notas", status_code=201)
def guardar_nota(cliente_id: int, nota: NotaIn):
    _cliente(cliente_id)
    NOTAS.setdefault(cliente_id, []).append({"fecha": str(date.today()), "texto": nota.texto})
    return NOTAS[cliente_id][-1]
~~~

**Paso 2 · Dos herramientas: las escribes tú (25 min).** En `agent/tools.py`:

~~~python
# TODO: ver_notas(cliente_id: int) → GET /clientes/{id}/notas
#       Docstring: "Notas de conversaciones anteriores con este cliente. Léelas al identificarlo."
# TODO: guardar_nota(cliente_id: int, texto: str) → POST /clientes/{id}/notas con json={"texto": texto}
#       Docstring: "Guarda en una frase lo ocurrido en esta conversación, al terminar la gestión."
# Añádelas a TOOLS.
~~~

<details>
<summary>Solución</summary>

~~~python
@tool
def ver_notas(cliente_id: int) -> str:
    """Notas de conversaciones anteriores con este cliente. Léelas justo después de identificarlo."""
    return _llamar("GET", f"/clientes/{cliente_id}/notas")


@tool
def guardar_nota(cliente_id: int, texto: str) -> str:
    """Guarda en una frase lo ocurrido en esta conversación, al terminar la gestión."""
    return _llamar("POST", f"/clientes/{cliente_id}/notas", json={"texto": texto})
~~~
</details>

**Paso 3 · Reglas (5 min).** Añade al `SYSTEM` de `agent/graph.py`:

```
6. Justo después de identificar al cliente, lee sus notas con ver_notas y tenlas en cuenta.
7. Cuando termines una gestión (ticket creado, duda resuelta), guarda una nota breve con guardar_nota.
```

**Prueba (20 min).** Dos conversaciones en **hilos distintos** con el mismo cliente:

1. Hilo A: el cliente se queja de un pedido retrasado → crea ticket → sal.
2. Hilo B (nuevo): el mismo cliente dice "hola, vuelvo a escribir".

**Está bien si** en el hilo B el agente sabe que ya hay un ticket por ese retraso, sin que el cliente lo diga.

```bash
git add -A && git commit -m "Support agent: memoria de cliente con notas en el CRM"
```

---

### Sábado 1 · 1,5 h

**Técnico, 30 min · Aprobación humana.**

1. En `agent/tools.py`, cambia `actualizar_ticket` para que pida permiso **antes** de tocar nada:

    ~~~python
    from langgraph.types import interrupt


    @tool
    def actualizar_ticket(ticket_id: int, estado: str, comentario: str | None = None) -> str:
        """Cambia el estado de un ticket a 'abierto', 'en_curso' o 'resuelto'. Requiere aprobación de un supervisor."""
        decision = interrupt({"accion": "actualizar_ticket", "ticket_id": ticket_id,
                              "estado": estado, "comentario": comentario})
        if decision != "si":
            return "Acción no aprobada por el supervisor. Dile al cliente que un compañero lo revisará."
        return _llamar("PATCH", f"/tickets/{ticket_id}", json={"estado": estado, "comentario": comentario})
    ~~~

2. En `agent/chat.py`, gestiona la pausa. Pon arriba `from langgraph.types import Command` y, dentro del bucle `while`, sustituye la línea `resultado = app.invoke(...)` y la siguiente por:

    ~~~python
            resultado = app.invoke({"messages": [("user", texto)]}, config)
            while "__interrupt__" in resultado:  # el agente espera una decisión humana
                peticion = resultado["__interrupt__"][0].value
                print(f"\n⚠️  Supervisor: el agente quiere {peticion}")
                decision = input("¿Apruebas? (si/no): ").strip().lower()
                resultado = app.invoke(Command(resume=decision), config)
            print(f"Agente: {resultado['messages'][-1].content}\n")
    ~~~

3. **Prueba los dos caminos:** pide cerrar un ticket y responde **si** (en `localhost:8001/clientes/<id>/tickets` sale "resuelto"); luego otro con **no** (el estado no cambia y el agente lo explica al cliente).

**Carrera, 1 h · 2 candidaturas.**

---

### Domingo 2 · 15 min · Cierre y checkpoint de abril

1. **Checkpoint:** fin de S27 en la tabla del roadmap: agente con CRM, memoria y aprobación; 42 problemas, 23 candidaturas y 10 contactos.
2. Añade al README del proyecto 03 una sección **Memory & human approval** con 3 líneas.
3. Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] Una conversación se retoma por su hilo tras reiniciar
- [ ] El agente lee y guarda notas del cliente entre hilos distintos
- [ ] `actualizar_ticket` pide aprobación y respeta el "no"
- [ ] El `interrupt` está antes de cualquier efecto
- [ ] 2 problemas de programación dinámica y 2 candidaturas

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `connection refused` en el 5434 | Falta `docker compose up -d` en `projects/03-support-agent`. |
| El agente no recuerda en el mismo hilo | Comprueba que pasas el mismo `thread_id` y que compilas el grafo con `checkpointer=`. |
| `RuntimeError` al usar `interrupt` | `interrupt` solo funciona si el grafo tiene checkpointer. |
| No aparece `__interrupt__` en el resultado | Versión antigua de LangGraph: actualízala (`uv add langgraph --upgrade`) o consulta `app.get_state(config).next`. |
| Las notas desaparecen | El CRM guarda en memoria y se borra al reiniciarlo. Es aceptable para la demo; anótalo como limitación. |
