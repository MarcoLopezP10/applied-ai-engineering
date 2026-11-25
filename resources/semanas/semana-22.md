# Semana 22 · 22–28 mar · Feedback, métricas finales y write-up

[← Semana 21](semana-21.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 23 →](semana-23.md)

🎯 **Objetivo:** convertir DocuChat en una **historia con números**: qué problema resuelve, para quién, qué decidiste y por qué, cómo de bien funciona y qué aprendiste de usuarios reales. Es el documento que enlazarás en cada candidatura.

> **Semana Santa 2027:** el Domingo de Resurrección es el 28 de marzo. Si esta semana tienes vacaciones, sube a 8 h y adelanta el vídeo de la semana 23.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 23 | 1 h | Técnico | Analizar el feedback y elegir una mejora |
| Miércoles 24 | 1 h | Algoritmos | Subsets y Combination Sum |
| Jueves 25 | 1 h | Técnico | Implementar la mejora y sacar las métricas finales |
| Sábado 27 | 1,5 h | Técnico + carrera | Write-up (30 min) + 1 candidatura (1 h) |
| Domingo 28 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**Priorizar feedback.** Te dirán 10 cosas. Se clasifican por **impacto** (a cuántos afecta y cuánto) y **esfuerzo**, y se hace la de más impacto y menos esfuerzo. Las demás se apuntan como "next steps". Es lo que hace un FDE cada semana con un cliente.

**Un write-up de ingeniería** no es un README. El README dice cómo usarlo; el write-up cuenta **por qué es así**: decisiones, alternativas descartadas, resultados y errores. Es lo que leen los ingenieros que te entrevistan antes de la entrevista técnica.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana22-writeup
```

---

### Martes 23 · 1 h · Analizar el feedback

1. **Junta las fuentes (15 min):**
    - Respuestas del formulario.
    - Langfuse: trazas de los usuarios. Filtra las respuestas "No lo encuentro" y las de más latencia.
    - Lo que te hayan dicho por mensaje.
2. **Clasifica (25 min).** En `docs/notas.md`:

    | # | Problema o petición | Cuántos lo dicen | Impacto (1-3) | Esfuerzo (1-3) | ¿Lo hago? |
    |---|---|:---:|:---:|:---:|:---:|

    Ejemplos de lo que suele salir: "se abstiene demasiado", "tarda mucho en subir el PDF", "responde en inglés si pregunto en español", "no sé qué documentos tengo subidos", "quiero borrar un PDF".

3. **Elige una (20 min)**: la de más impacto y menos esfuerzo. Escribe en 3 líneas qué vas a cambiar y **cómo sabrás que ha mejorado**. Por ejemplo: "repetir el eval y que la abstención en preguntas que sí están baje de X a Y".

---

### Miércoles 24 · 1 h · Algoritmos (Backtracking)

**Subsets** (Medium) → `practice/algoritmos/subsets.py`

~~~python
def subsets(nums: list[int]) -> list[list[int]]:
    ...


if __name__ == "__main__":
    assert sorted(map(sorted, subsets([1, 2, 3]))) == sorted(map(sorted, [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]))
    print("OK")
~~~

**Combination Sum** (Medium) → `practice/algoritmos/combination_sum.py`

~~~python
def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    ...


if __name__ == "__main__":
    assert sorted(map(sorted, combination_sum([2, 3, 6, 7], 7))) == [[2, 2, 3], [7]]
    assert sorted(map(sorted, combination_sum([2, 3, 5], 8))) == [[2, 2, 2, 2], [2, 3, 3], [3, 5]]
    print("OK")
~~~

<details>
<summary>Pista (backtracking)</summary>
Una función recursiva que recibe "desde qué índice puedo elegir" y "lo que llevo elegido". En cada paso, o eliges el elemento y sigues, o no lo eliges y pasas al siguiente. En Combination Sum puedes repetir el mismo elemento, así que al elegirlo no avanzas el índice.
</details>

---

### Jueves 25 · 1 h · Mejora y métricas finales

1. **Implementa la mejora (35 min)**, con test si se puede, y despliégala con PR y merge.
2. **Métricas finales (25 min).** Ejecuta el eval con la configuración de producción y reúne en `docs/notas.md`:

    | Métrica | Valor | Fuente |
    |---|:---:|---|
    | hit@5 | | eval |
    | Corrección media (1-3) | | eval |
    | Fidelidad media | | eval |
    | Abstención correcta en trampas | | eval |
    | Latencia p50 / p95 | | eval |
    | Coste por pregunta | | eval |
    | Usuarios reales | 5 | — |
    | Preguntas reales hechas | | Langfuse |
    | % de respuestas "No lo encuentro" en uso real | | Langfuse |
    | Valoración media de utilidad (1-5) | | formulario |
    | Coste total del mes en AWS | | AWS Billing |

---

### Sábado 27 · 1,5 h

**Técnico, 30 min · Write-up.** Crea `projects/02-docuchat/WRITEUP.md`, en inglés y de una página. Rellena cada sección con tus datos reales:

```markdown
# DocuChat: cited answers over your own PDFs

## Problem
Students waste time searching long lecture PDFs. Generic chatbots answer from memory and can't be checked.
DocuChat answers only from your documents and cites the page.

## Users
5 MSc classmates used it for one week with their own lecture notes: N questions, rated X/5 for usefulness.

## Architecture
React (Vercel) → FastAPI (Docker on EC2, Caddy HTTPS) → PostgreSQL + pgvector (Supabase) · Gemini (LLM + embeddings) · Langfuse (tracing) · GitHub Actions (CI/CD to ECR + SSM)

## Key decisions (with data)
1. **Chunking:** sentence-based vs fixed 1000/150 → chose X because hit@5 went from A to B.
2. **Model:** X vs Y → chose X: similar correctness, N× cheaper, p95 latency M s.
3. **Hybrid search:** kept / dropped because hit@5 changed from A to B on a 30-question golden set.

## Results
| hit@5 | Correctness | Faithfulness | Abstains on traps | p50 / p95 | Cost/question |
|---|---|---|---|---|---|

## What went wrong
- (a real failure and what you learned: e.g. users asked in Spanish about English notes → keyword search useless)

## What I'd do next
- Store PDFs in S3 to open the exact page · Alembic migrations · OIDC for CI · reranking
```

Enlázalo desde el README de DocuChat y desde el principal.

**Carrera, 1 h · 1 candidatura**, enlazando el write-up.

---

### Domingo 28 · 15 min · Cierre

1. Escribe a los 5 compañeros para darles las gracias y contarles qué has cambiado gracias a ellos.
2. Log semanal.
3. PR y merge.

---

✅ **Checklist**
- [ ] Feedback clasificado por impacto y esfuerzo
- [ ] Una mejora hecha y medida
- [ ] Tabla de métricas finales completa
- [ ] WRITEUP.md de una página, enlazado
- [ ] 2 problemas de backtracking y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| Solo han respondido 2 de 5 al formulario | Úsalo igual y dilo tal cual en el write-up ("2 of 5 answered"). La honestidad con los números cuenta a favor. |
| No sabes qué poner en "What went wrong" | Mira tus notas de las semanas 11–15: preguntas que fallaban, la búsqueda híbrida que no mejoró, el error de CORS. Cualquiera vale si cuentas qué aprendiste. |
| El write-up ocupa 3 páginas | Recorta las secciones Architecture y Key decisions a 3 líneas cada una. Una página de verdad. |
