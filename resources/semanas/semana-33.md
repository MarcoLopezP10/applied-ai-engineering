# Semana 33 · 7–13 jun · Write-up, vídeo, impacto y pitch

[← Semana 32](semana-32.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 34 →](semana-34.md)

🎯 **Objetivo:** saber **vender** el agente: un write-up de una página, un vídeo de 2 minutos, una cifra de impacto en negocio con sus supuestos y un pitch de 2 y de 10 minutos ensayado en inglés. Según tu test, presentar el ahorro a un director es lo único de FDE que no te atrae, y es justo lo que más se valora. Esta semana se entrena.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 8 | 1 h | Técnico | Cálculo de impacto (ROI) |
| Miércoles 9 | 1 h | Algoritmos | 2 de repaso |
| Jueves 10 | 1 h | Técnico | Write-up de una página |
| Sábado 12 | 1,5 h | Técnico + carrera | Vídeo (30 min) + pitch grabado y 1 candidatura (1 h) |
| Domingo 13 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**Un número de impacto honesto.** "Mi agente ahorra 40.000 € al año" no vale nada sin sus supuestos. Lo que impresiona en una entrevista es:

1. Los **supuestos** escritos (tickets al mes, minutos por ticket, coste de una hora de soporte).
2. Qué dato sale de **tu medición** (tasa de éxito y coste por tarea, de la semana 31).
3. Un **análisis de sensibilidad**: "si la tasa de éxito real fuera la mitad, seguiría ahorrando X".

**Pitch en dos tamaños.** El de 2 minutos responde a "cuéntame un proyecto" en cualquier entrevista. El de 10 minutos es para la entrevista técnica, cuando quieren entrar en detalle. Ambos siguen la misma estructura: problema → solución → resultado → qué aprendí.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana33-writeup-agente
```

---

### Martes 8 · 1 h · Cálculo de impacto

Crea `projects/03-support-agent/docs/impacto.md` y rellénalo:

```markdown
# Impacto estimado del agente de soporte en TechStore

## Supuestos (cambiables)
| Variable | Valor | De dónde sale |
|---|---|---|
| Tickets al mes (T) | 2.000 | Supuesto: tienda online mediana |
| % de tickets de tipo consulta/estado/políticas (P) | 60 % | Supuesto |
| Tasa de éxito del agente en esos casos (E) | __ % | **Mi eval, semana 31** |
| Minutos de una persona por ticket (M) | 8 | Supuesto |
| Coste por hora de una persona de soporte, con cargas (C) | 22 € | Supuesto |
| Coste del agente por ticket (L) | __ € | **Mi eval: tokens × precio** |

## Cálculo
Tickets resueltos por el agente = T × P × E = __
Ahorro por ticket = (M / 60) × C − L = __ €
**Ahorro mensual = tickets resueltos × ahorro por ticket = __ €**  (≈ __ € al año)

## Sensibilidad
| Si… | Ahorro mensual |
|---|---|
| E fuera la mitad | __ € |
| M fuera 4 minutos | __ € |
| El coste del LLM se multiplicara por 10 | __ € |

## Lo que no está en el cálculo
- Respuesta inmediata 24/7 (mejor experiencia de cliente)
- Coste de supervisar las aprobaciones humanas
- Coste de mantener el sistema (infraestructura, evals)
```

Hazlo con una calculadora o con 5 líneas de Python. Fíjate en el resultado: aunque el coste del LLM se multiplique por 10, normalmente apenas cambia nada, porque el coste dominante es el tiempo de las personas. Es una buena frase para una entrevista.

---

### Miércoles 9 · 1 h · Algoritmos

2 problemas de repaso de los que más te costaron. Lleva la cuenta: deberías estar cerca de 50 en total.

---

### Jueves 10 · 1 h · Write-up de una página

`projects/03-support-agent/WRITEUP.md`, en inglés, con la misma estructura que el de DocuChat más dos secciones propias de un agente:

```markdown
# Support Agent for TechStore (fictional client)

## Problem
## Solution
LangGraph agent over the client's CRM (mock API): identifies customers, checks orders, creates tickets,
answers policy questions through an MCP server backed by DocuChat, and asks a human before changing data.

## Architecture
(services diagram from week 32)

## Key decisions
1. Workflow for webhook triage, agent for conversations (why)
2. Human approval via interrupt before any write
3. MCP so the same knowledge tool works in my agent and in Claude Code

## Safety
Least privilege · data/instruction separation · injection detector → human review · PII masking · token caps · AI disclosure

## Evaluation
20 deterministic scenarios: X % success, Y tool calls on average, p50 Z s, ~W tokens/task. Model comparison table.

## Business impact (assumptions in docs/impacto.md)
~N € per month for a 2,000-ticket/month store; still positive if success rate halves.

## What went wrong / What I'd do next
```

Enlázalo desde el README del proyecto 03 y desde el README principal, y marca el proyecto 03 como **Done**.

---

### Sábado 12 · 1,5 h

**Técnico, 30 min · Vídeo de 2 minutos.** Mismo método que en DocuChat (semana 23):

| Tiempo | Qué se ve | Qué dices |
|---|---|---|
| 0:00–0:15 | — | El problema de TechStore |
| 0:15–1:15 | Demo web: cliente con pedido retrasado → ticket; pregunta de política → cita; cerrar ticket → aprobación → rechazar | Qué hace y por qué la aprobación humana |
| 1:15–1:45 | Tabla de evals e impacto | "X % of 20 scenarios, ~N € per month under stated assumptions" |
| 1:45–2:00 | Diagrama | Una decisión técnica |

Súbelo y enlázalo en el README y en "Destacado" de LinkedIn.

**Carrera, 1 h:**

1. **Pitch (40 min).** Escribe los dos pitches en un documento privado. Después **grábate en el móvil** diciendo el de 2 minutos, en inglés y sin leer. Escúchalo: ¿se entiende el problema en los primeros 15 segundos? ¿Dices una cifra? Repite hasta que te salga en 2 minutos.

    - **Pitch de 2 minutos:** problema (20 s) → qué construí (40 s) → resultado con números (30 s) → qué aprendí (30 s).
    - **Pitch de 10 minutos:** lo mismo más arquitectura (2 min), 2 decisiones con alternativas (3 min), un fallo real y cómo lo resolví (2 min) y qué haría con más tiempo (1 min).

2. **1 candidatura** (20 min).

---

### Domingo 13 · 15 min · Cierre

Log semanal, PR y merge.

---

✅ **Checklist**
- [ ] Impacto con supuestos, datos de tu eval y sensibilidad
- [ ] WRITEUP.md de una página enlazado; proyecto 03 en Done
- [ ] Vídeo de 2 minutos publicado
- [ ] Pitch de 2 minutos grabado y repetido hasta que sale fluido
- [ ] 2 problemas de repaso y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| La cifra de ahorro parece exagerada | Seguramente lo es: baja P (el % de tickets automatizables) y dilo. Mejor una cifra prudente que una que no aguanta una pregunta. |
| El pitch se te va a 4 minutos | Quita la arquitectura del de 2 minutos: solo problema, resultado y aprendizaje. |
| Te bloqueas hablando en inglés | Escribe las primeras frases de cada parte y apréndelas de memoria. El resto sale solo. |
