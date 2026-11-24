# Semana 12 · 11–17 ene · Evals con LLM como juez

[← Semana 11](semana-11.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 13 →](semana-13.md)

🎯 **Objetivo:** medir no solo si se recupera la página buena, sino si la **respuesta es correcta** y si es **fiel a las fuentes** (no añade nada inventado). Empieza el term 2: vuelves a 4–5 h.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 12 | 1 h | Técnico | El juez: prompts y validación |
| Miércoles 13 | 1 h | Algoritmos | Binary Search y Search a 2D Matrix |
| Jueves 14 | 1 h | Técnico | Integrarlo en el eval y ejecutarlo |
| Sábado 16 | 1,5 h | Técnico + carrera | Revisar a mano al juez (30 min) + horas reales y 1 candidatura (1 h) |
| Domingo 17 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**LLM como juez.** Corregir a mano 30 respuestas cada vez que cambias algo es inviable. La solución habitual es pedirle a un LLM que corrija con una **rúbrica** clara y una salida estructurada. Es el mismo patrón de la semana 5 (Pydantic + reintento), aplicado a evaluar.

**Dos métricas distintas:**

- **Corrección:** ¿la respuesta dice lo mismo que la esperada? Rúbrica de 1 a 3.
- **Fidelidad (*faithfulness*):** ¿cada afirmación de la respuesta está en los fragmentos? Una respuesta puede ser correcta pero no fiel (la sacó de su conocimiento propio) o fiel pero incorrecta (los fragmentos eran malos).

**El juez también se equivoca.** Por eso se revisan a mano los casos dudosos y se usa siempre el **mismo juez** para comparar versiones. Si cambias el juez, los números dejan de ser comparables.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana12-llm-juez
cd projects/02-docuchat && docker compose up -d
```

---

### Martes 12 · 1 h · El juez

Crea `evals/juez.py`. Los prompts y los modelos de datos están hechos; la función `juzgar` la escribes tú, reutilizando lo que hiciste en el Code Analyzer de la semana 5:

~~~python
"""LLM como juez: corrección (1-3) y fidelidad a las fuentes."""
import json
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.llm import client

MODELO_JUEZ = "gemini-3.8-flash"  # FIJO: no cambia aunque cambies el modelo de DocuChat


class Correccion(BaseModel):
    score: Literal[1, 2, 3]
    motivo: str


class Afirmacion(BaseModel):
    texto: str
    respaldada: bool


class Fidelidad(BaseModel):
    afirmaciones: list[Afirmacion]


PROMPT_CORRECCION = """Eres un evaluador estricto. Compara la RESPUESTA con la RESPUESTA ESPERADA para la PREGUNTA.
Puntúa:
3 = correcta y completa (aunque use otras palabras)
2 = parcialmente correcta o le falta algo importante
1 = incorrecta, contradice la esperada o no responde
Devuelve solo JSON: {"score": 1, "motivo": "una frase"}"""

PROMPT_FIDELIDAD = """Te doy unos FRAGMENTOS y una RESPUESTA.
Divide la respuesta en afirmaciones simples. Para cada una, indica si está respaldada por los fragmentos
(true) o si añade algo que los fragmentos no dicen (false). Ignora las marcas de cita como [1].
Devuelve solo JSON: {"afirmaciones": [{"texto": "...", "respaldada": true}]}"""


def juzgar(modelo: type[BaseModel], system: str, user: str) -> BaseModel:
    # TODO: igual que analyze_code de la semana 5:
    #  - llamada con MODELO_JUEZ, temperature=0 y response_format JSON
    #  - valida con modelo.model_validate_json(texto)
    #  - si falla, reintenta UNA vez pasando el error; si vuelve a fallar, ValueError
    raise NotImplementedError


def corregir(pregunta: str, esperada: str, respuesta: str) -> Correccion:
    user = f"PREGUNTA: {pregunta}\nRESPUESTA ESPERADA: {esperada}\nRESPUESTA: {respuesta}"
    return juzgar(Correccion, PROMPT_CORRECCION, user)


def fidelidad(fragmentos: list[dict], respuesta: str) -> float:
    """Proporción de afirmaciones respaldadas (1.0 = totalmente fiel)."""
    contexto = "\n\n".join(f"[{f['n']}] {f['text']}" for f in fragmentos)
    resultado = juzgar(Fidelidad, PROMPT_FIDELIDAD, f"FRAGMENTOS:\n{contexto}\n\nRESPUESTA: {respuesta}")
    if not resultado.afirmaciones:
        return 1.0
    return sum(a.respaldada for a in resultado.afirmaciones) / len(resultado.afirmaciones)
~~~

<details>
<summary>Solución de juzgar</summary>

~~~python
def juzgar(modelo: type[BaseModel], system: str, user: str) -> BaseModel:
    mensajes = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for _ in range(2):
        r = client.chat.completions.create(
            model=MODELO_JUEZ, temperature=0, messages=mensajes,
            response_format={"type": "json_object"},
        )
        texto = r.choices[0].message.content
        try:
            return modelo.model_validate_json(texto)
        except ValidationError as error:
            mensajes += [
                {"role": "assistant", "content": texto},
                {"role": "user", "content": f"JSON no válido: {error}. Corrígelo y devuelve solo JSON."},
            ]
    raise ValueError("El juez no devolvió un JSON válido")
~~~
</details>

Pruébalo con un caso inventado. Desde `projects/02-docuchat`:

```bash
uv run python -c "
import sys; sys.path.insert(0, '.')
from evals.juez import corregir
print(corregir('¿Capital de Francia?', 'París', 'La capital es París.'))
print(corregir('¿Capital de Francia?', 'París', 'Es Lyon.'))"
```

**Está bien si** la primera da `score=3` y la segunda `score=1`. Si te da `ModuleNotFoundError: evals`, crea un archivo vacío `evals/__init__.py`.

```bash
git add -A && git commit -m "Evals: juez LLM de corrección y fidelidad"
```

---

### Miércoles 13 · 1 h · Algoritmos (patrón Binary Search)

**Binary Search** (Easy) → `practice/algoritmos/binary_search.py`

~~~python
def search(nums: list[int], target: int) -> int:
    """Índice de target en nums (ordenada) o -1. Debe ser O(log n)."""
    ...


if __name__ == "__main__":
    assert search([-1, 0, 3, 5, 9, 12], 9) == 4
    assert search([-1, 0, 3, 5, 9, 12], 2) == -1
    print("OK")
~~~

**Search a 2D Matrix** (Medium) → `practice/algoritmos/search_2d_matrix.py`

~~~python
def search_matrix(matrix: list[list[int]], target: int) -> bool:
    ...


if __name__ == "__main__":
    m = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_matrix(m, 3) is True
    assert search_matrix(m, 13) is False
    print("OK")
~~~

<details>
<summary>Pista</summary>
Trata la matriz como una lista ordenada de filas × columnas elementos. La posición i corresponde a matrix[i // columnas][i % columnas].
</details>

---

### Jueves 14 · 1 h · Integrarlo en el eval

En `evals/run_eval.py`:

1. Importa el juez: `from evals.juez import corregir, fidelidad` (añade `evals/__init__.py` si no existe).
2. Dentro del bucle, para las preguntas **que no son trampa** y en las que el sistema **no se abstuvo**, añade a la fila:

~~~python
            if not es_trampa and not se_abstiene:
                filas[-1]["correccion"] = corregir(caso["question"], caso["expected_answer"], r["answer"]).score
                filas[-1]["fidelidad"] = round(fidelidad(r["retrieved"], r["answer"]), 2)
~~~

3. En el resumen, añade:

~~~python
    juzgadas = [f for f in normales if "correccion" in f]
    resumen["correccion_media"] = round(sum(f["correccion"] for f in juzgadas) / max(len(juzgadas), 1), 2)
    resumen["fidelidad_media"] = round(sum(f["fidelidad"] for f in juzgadas) / max(len(juzgadas), 1), 2)
~~~

Ejecuta `uv run python evals/run_eval.py`. Ahora tarda más: hasta 4 llamadas por pregunta.

**Está bien si** el JSON de `evals/results/` tiene 5 métricas: `hit@5`, `abstiene_en_trampas`, `responde_cuando_debe`, `correccion_media` y `fidelidad_media`.

```bash
git add -A && git commit -m "Evals: corrección y fidelidad en el eval"
```

---

### Sábado 16 · 1,5 h

**Técnico, 30 min · Juzgar al juez.** Abre el último resultado y elige 5 casos al azar. Para cada uno, lee la pregunta, la respuesta y la esperada y decide **tú** la nota de 1 a 3. Apunta en `docs/notas.md`:

| id | Mi nota | Nota del juez | ¿De acuerdo? | Por qué discrepamos |
|---|:---:|:---:|:---:|---|

Si discrepáis en 2 o más, mejora `PROMPT_CORRECCION` con un ejemplo de cada nota (few-shot) y repite. Esto es exactamente lo que se hace en las empresas antes de fiarse de un juez automático.

**Carrera, 1 h:**

1. **Horas reales (10 min).** Apunta en el log cuántas horas hiciste esta semana y en qué bloque. La semana que viene, otra vez. Si salen menos de 4, recorta el técnico de las próximas semanas (no algoritmos ni carrera).
2. **1 candidatura de la ola 2 (50 min).** Elige de tu Excel una empresa de la ola 2 con oferta abierta. Mismo método: 5 palabras clave, 3 cambios en el CV, enviar y apuntar con follow-up a +10 días.

---

### Domingo 17 · 15 min · Cierre

1. Actualiza la sección **Evaluation** del README de DocuChat con las 5 métricas y la fecha.
2. Log semanal.
3. En Claude Code:
    ```
    Cerramos la semana 12. Revisa el checklist de resources/semanas/semana-12.md
    y dime qué falta. Luego commit, push de semana12-llm-juez, PR, mergea y deja main al día.
    ```

---

✅ **Checklist**
- [ ] Juez de corrección y de fidelidad con salida validada
- [ ] Eval con 5 métricas guardadas por fecha
- [ ] 5 casos revisados a mano contra el juez
- [ ] Horas reales apuntadas
- [ ] 2 problemas de Binary Search
- [ ] 1 candidatura de la ola 2

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| El juez pone 3 a todo | Rúbrica demasiado blanda: añade ejemplos de un 1 y de un 2 en el prompt. |
| La fidelidad sale siempre 1.0 | El juez no está dividiendo en afirmaciones. Pídele "mínimo una afirmación por frase". |
| Error 429 durante el eval | Son muchas llamadas seguidas. Añade `time.sleep(1)` entre preguntas. |
| El eval tarda más de 10 minutos | Normal con un modelo saturado. Para pruebas rápidas, filtra los 10 primeros casos con una variable `LIMITE`. |
