# Semana 11 · 4–10 ene · DocuChat v0: respuestas con citas + primer eval

[← Semana 10](semana-10.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 12 →](semana-12.md)

🎯 **Objetivo:** DocuChat responde preguntas usando solo tus documentos, cita la página de donde saca cada cosa, dice "no lo encuentro" cuando no está, y tienes tu **primer número de calidad**.

**Última semana de vacaciones: unas 10 h.** El miércoles 6 (Reyes) es libre.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Lunes 4 | 2,5 h | Técnico | Generación con citas y `POST /ask` |
| Martes 5 | 2,5 h | Técnico | Golden set de 30 preguntas |
| Jueves 7 | 2 h + 1 h | Técnico + algoritmos | Eval v0 (hit@5) y tests + Valid Parentheses |
| Viernes 8 | 2 h | Algoritmos + carrera | Min Stack + LinkedIn, GitHub y 2 mensajes |
| Domingo 10 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**Generación aumentada (la G de RAG).** Le pasas al LLM la pregunta y los 5 fragmentos encontrados, numerados, con una regla clara: responde solo con eso y cita el número. Así puedes comprobar cada afirmación.

**Abstenerse es una función, no un fallo.** Un buen sistema RAG dice "no lo encuentro" cuando la respuesta no está. Inventar una respuesta convincente (alucinar) es el peor error posible en una empresa.

**Golden set.** Una lista fija de preguntas con su respuesta correcta y dónde está. Es tu examen: cada vez que cambias algo (troceado, modelo, prompt), lo repites y ves si mejora o empeora. Sin esto, "parece que va mejor" no vale nada.

**hit@5.** El porcentaje de preguntas en las que la página correcta aparece entre los 5 fragmentos recuperados. Si la búsqueda no trae la página buena, el LLM no puede acertar: es lo primero que se mide.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana11-docuchat-ask
cd projects/02-docuchat
docker compose up -d
```

---

### Lunes 4 · 2,5 h · Generación con citas

**Paso 1 · El prompt (20 min).** Crea `app/generate.py`. Lee el prompt con atención: cada regla existe por un motivo.

~~~python
"""Generación: responde con los fragmentos recuperados y cita las fuentes."""
import re

from sqlalchemy.orm import Session

from app.config import settings
from app.llm import client
from app.retrieval import buscar

NO_ENCONTRADO = "No lo encuentro en los documentos."

SYSTEM_PROMPT = f"""Eres DocuChat, un asistente que responde preguntas usando SOLO los fragmentos de documentos que se te dan.

Reglas:
1. Responde en el idioma de la pregunta, de forma clara y breve.
2. Después de cada frase que use información de un fragmento, cita su número entre corchetes, por ejemplo [1] o [2][3].
3. Si los fragmentos no contienen la respuesta, responde exactamente: "{NO_ENCONTRADO}"
4. No uses conocimiento propio ni inventes datos que no estén en los fragmentos."""


def construir_contexto(fragmentos: list[dict]) -> str:
    """Numera los fragmentos para que el modelo pueda citarlos."""
    return "\n\n".join(
        f"[{i}] ({f['document']}, pág. {f['page']})\n{f['text']}"
        for i, f in enumerate(fragmentos, start=1)
    )


def extraer_citas(respuesta: str) -> list[int]:
    """Devuelve los números citados, sin repetir y en orden: '[2] y [1][2]' → [1, 2]."""
    return sorted({int(n) for n in re.findall(r"\[(\d+)\]", respuesta)})
~~~

**Paso 2 · La función principal: la escribes tú (50 min).** Añade a `app/generate.py`:

~~~python
def responder(session: Session, pregunta: str, k: int = 5) -> dict:
    # TODO:
    # 1. fragmentos = buscar(session, pregunta, k)
    # 2. Llama al modelo (client.chat.completions.create) con:
    #      - model=settings.chat_model, temperature=0.1 (queremos precisión, no creatividad)
    #      - system: SYSTEM_PROMPT
    #      - user: f"Fragmentos:\n{construir_contexto(fragmentos)}\n\nPregunta: {pregunta}"
    # 3. citas = extraer_citas(texto de la respuesta)
    # 4. Devuelve:
    #    {"answer": texto,
    #     "sources": [fragmentos citados, cada uno con su número "n"],
    #     "retrieved": [todos los fragmentos recuperados con su "n"]}
    #    Ojo: si el modelo cita [7] pero solo hay 5 fragmentos, ignora esa cita.
    raise NotImplementedError
~~~

<details>
<summary>Solución</summary>

~~~python
def responder(session: Session, pregunta: str, k: int = 5) -> dict:
    fragmentos = buscar(session, pregunta, k)
    respuesta = client.chat.completions.create(
        model=settings.chat_model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Fragmentos:\n{construir_contexto(fragmentos)}\n\nPregunta: {pregunta}"},
        ],
    )
    texto = respuesta.choices[0].message.content.strip()
    numerados = [{"n": i, **f} for i, f in enumerate(fragmentos, start=1)]
    citas = [n for n in extraer_citas(texto) if 1 <= n <= len(numerados)]
    return {
        "answer": texto,
        "sources": [numerados[n - 1] for n in citas],
        "retrieved": numerados,
    }
~~~
</details>

**Paso 3 · El endpoint (20 min).** En `app/main.py`:

~~~python
from pydantic import BaseModel, Field

from app.generate import responder


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    k: int = Field(default=5, ge=1, le=10)


@app.post("/ask")
def ask(body: AskRequest, session: Session = Depends(get_session)):
    return responder(session, body.question, body.k)
~~~

`Field` valida la entrada: una pregunta vacía o de 10.000 caracteres se rechaza con un error 422 antes de gastar una llamada al modelo.

**Paso 4 · Probarlo de verdad (60 min).** Arranca con `uv run uvicorn app.main:app --reload` y, en `/docs`, haz 10 preguntas:

- 5 cuya respuesta sabes que está en tus PDFs.
- 3 que estén en los PDFs pero con otras palabras.
- 2 que **no** estén (por ejemplo, "¿quién ganó el Mundial de 2010?").

Para cada una, comprueba en el PDF que la página citada es correcta. Apunta en `docs/notas.md` cuántas acertó, cuántas citó bien y si alguna vez se inventó algo. Estas notas son el germen de tus evals.

```bash
git add -A && git commit -m "DocuChat: /ask con citas y abstención"
```

---

### Martes 5 · 2,5 h · Golden set

Es la tarea más aburrida de la semana y la más valiosa. Con ella podrás demostrar con números todo lo que hagas en los próximos tres meses.

**Paso 1 · Formato.** Crea `evals/golden_set.jsonl`, con una pregunta por línea en JSON:

```json
{"id": 1, "question": "¿Qué diferencia hay entre varianza muestral y poblacional?", "expected_answer": "La muestral divide entre n-1 y la poblacional entre n.", "document": "estadistica_tema2.pdf", "page": 14}
{"id": 26, "question": "¿Cuál es la capital de Australia?", "expected_answer": null, "document": null, "page": null}
```

**Paso 2 · Las 30 preguntas (2 h).** Con 2–3 PDFs de clase abiertos:

| Tipo | Cuántas | Ejemplo |
|---|:---:|---|
| Definición directa | 8 | "¿Qué es un data warehouse?" |
| Dato concreto (número, fecha, nombre) | 6 | "¿Cuántas formas normales se ven en el tema 3?" |
| Dicho con otras palabras | 6 | Pregunta por un concepto sin usar las palabras del PDF |
| Necesita juntar dos partes | 5 | "¿Qué diferencia hay entre X e Y?" |
| **Trampa: no está en los documentos** | 5 | Preguntas del mismo tema, pero que tus PDFs no responden |

Reglas para que el examen sea bueno:

- Escribe las preguntas **en el idioma de los PDFs** (si tus apuntes del máster están en inglés, en inglés). La búsqueda por significado funciona entre idiomas, pero la búsqueda por palabras de la semana 15 no.
- Mira la página exacta donde está cada respuesta. Si está en dos páginas, pon la principal.
- No copies frases del PDF en la pregunta: eso hace que la búsqueda sea artificialmente fácil.
- Las trampas deben ser del mismo tema (por ejemplo, de estadística, pero de algo que tus apuntes no cubren). Si son de fútbol, son demasiado fáciles.

Los PDFs del máster son tuyos para estudiar, pero no los subas al repo. Añade esta línea al `.gitignore` del proyecto:

```
docs/pdfs/
```

Guárdalos en `projects/02-docuchat/docs/pdfs/`.

```bash
git add -A && git commit -m "DocuChat: golden set de 30 preguntas"
```

---

### Jueves 7 · 3 h · Eval v0, tests y algoritmos

**Paso 1 · El script de eval (60 min).** Crea `evals/run_eval.py`. Escribes tú `pagina_recuperada`; el resto está hecho:

~~~python
"""Eval v0 de DocuChat: hit@5 y abstención sobre el golden set."""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # para importar app/

from app.db import SessionLocal  # noqa: E402
from app.generate import NO_ENCONTRADO, responder  # noqa: E402

GOLDEN = Path(__file__).parent / "golden_set.jsonl"
RESULTADOS = Path(__file__).parent / "results"


def pagina_recuperada(caso: dict, recuperados: list[dict]) -> bool:
    # TODO: True si algún fragmento recuperado es del mismo documento
    #       y la misma página que caso["document"] y caso["page"].
    raise NotImplementedError


def main() -> None:
    casos = [json.loads(linea) for linea in GOLDEN.read_text(encoding="utf-8").splitlines() if linea.strip()]
    filas = []
    with SessionLocal() as session:
        for caso in casos:
            r = responder(session, caso["question"])
            se_abstiene = NO_ENCONTRADO.lower().rstrip(".") in r["answer"].lower()
            es_trampa = caso["page"] is None
            filas.append({
                "id": caso["id"],
                "trampa": es_trampa,
                "hit@5": None if es_trampa else pagina_recuperada(caso, r["retrieved"]),
                "abstencion_correcta": se_abstiene if es_trampa else not se_abstiene,
                "respuesta": r["answer"],
            })
            print(f"{caso['id']:>3} {'OK ' if filas[-1]['abstencion_correcta'] else 'MAL'} {caso['question'][:60]}")

    normales = [f for f in filas if not f["trampa"]]
    trampas = [f for f in filas if f["trampa"]]
    resumen = {
        "fecha": str(date.today()),
        "hit@5": round(sum(f["hit@5"] for f in normales) / len(normales), 3),
        "abstiene_en_trampas": round(sum(f["abstencion_correcta"] for f in trampas) / max(len(trampas), 1), 3),
        "responde_cuando_debe": round(sum(f["abstencion_correcta"] for f in normales) / len(normales), 3),
    }
    print("\n", json.dumps(resumen, indent=2, ensure_ascii=False))
    RESULTADOS.mkdir(exist_ok=True)
    (RESULTADOS / f"{date.today()}.json").write_text(
        json.dumps({"resumen": resumen, "casos": filas}, indent=2, ensure_ascii=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
~~~

<details>
<summary>Solución de pagina_recuperada</summary>

~~~python
def pagina_recuperada(caso: dict, recuperados: list[dict]) -> bool:
    return any(f["document"] == caso["document"] and f["page"] == caso["page"] for f in recuperados)
~~~
</details>

Ejecuta `uv run python evals/run_eval.py`. Tarda un par de minutos (30 preguntas con 2 llamadas cada una).

**Paso 2 · Leer los resultados (20 min).** Abre el JSON de `evals/results/` y mira los fallos uno a uno. Para cada uno, apunta en `docs/notas.md` si es:

- **Fallo de búsqueda:** la página buena no estaba en el top 5.
- **Fallo de generación:** la página estaba, pero respondió mal o se abstuvo.
- **Fallo del golden set:** tu pregunta o tu página esperada estaban mal.

Esta clasificación te dirá qué mejorar en las semanas 14 y 15.

**Paso 3 · Tests sin API ni base de datos (40 min).** Crea `tests/test_generate.py`:

~~~python
import os

os.environ.setdefault("GOOGLE_API_KEY", "clave-de-test")

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from app.generate import construir_contexto, extraer_citas  # noqa: E402


def test_extraer_citas_sin_repetir_y_ordenadas():
    assert extraer_citas("Es así [2]. También [1][2].") == [1, 2]


def test_sin_citas():
    assert extraer_citas("No lo encuentro en los documentos.") == []


def test_contexto_numerado_con_pagina():
    contexto = construir_contexto([{"document": "a.pdf", "page": 3, "text": "hola"}])
    assert contexto.startswith("[1] (a.pdf, pág. 3)")


def test_endpoint_ask_valida_y_responde(monkeypatch):
    falso = {"answer": "Sí [1]", "sources": [], "retrieved": []}
    monkeypatch.setattr(main, "responder", lambda session, pregunta, k: falso)
    main.app.dependency_overrides[main.get_session] = lambda: None
    cliente = TestClient(main.app)  # sin "with": no arranca lifespan ni toca la BD
    assert cliente.post("/ask", json={"question": "¿hola?"}).json() == falso
    assert cliente.post("/ask", json={"question": ""}).status_code == 422
~~~

```bash
uv run pytest -v
```

**Está bien si** salen 9 tests en verde: 5 de `trocear` y 4 nuevos.

**Paso 4 · Algoritmos (1 h). Valid Parentheses** (Easy, patrón Stack) → `practice/algoritmos/valid_parentheses.py`

~~~python
def is_valid(s: str) -> bool:
    ...


if __name__ == "__main__":
    assert is_valid("()[]{}") is True
    assert is_valid("(]") is False
    assert is_valid("([)]") is False
    assert is_valid("{[]}") is True
    print("OK")
~~~

<details>
<summary>Pista</summary>
Apila cada apertura. Con cada cierre, la cima de la pila tiene que ser su pareja.
</details>

```bash
git add -A && git commit -m "DocuChat: eval v0 (hit@5 y abstención) y tests"
```

---

### Viernes 8 · 2 h · Algoritmos + carrera

**Algoritmos (1 h). Min Stack** (Medium) → `practice/algoritmos/min_stack.py`

~~~python
class MinStack:
    def __init__(self):
        ...

    def push(self, val: int) -> None:
        ...

    def pop(self) -> None:
        ...

    def top(self) -> int:
        ...

    def get_min(self) -> int:
        ...


if __name__ == "__main__":
    s = MinStack()
    s.push(-2); s.push(0); s.push(-3)
    assert s.get_min() == -3
    s.pop()
    assert s.top() == 0 and s.get_min() == -2
    print("OK")
~~~

<details>
<summary>Pista</summary>
Todas las operaciones tienen que ser O(1). Guarda junto a cada valor cuál era el mínimo en ese momento.
</details>

**Carrera (1 h):**

1. **README de perfil de GitHub (25 min).** Crea un repo público llamado exactamente `MarcoLopezP10`. Su `README.md` aparece en tu perfil:

    ```markdown
    ### Hi, I'm Marco 👋
    Computer Engineer (CUNEF) · MSc Business Analytics & Data Science (IE) · Madrid

    I build applied AI systems: LLM apps, RAG, agents and the engineering to run them in production.

    **Currently building:** [DocuChat](https://github.com/MarcoLopezP10/applied-ai-engineering/tree/main/projects/02-docuchat), RAG over PDFs with cited answers and evals.

    **Stack:** Python · FastAPI · PostgreSQL/pgvector · Docker · LLM APIs · Git/GitHub Actions

    📫 [LinkedIn](https://www.linkedin.com/in/marco-lopez-prieto-320810384/)
    ```

    En tu perfil, "Customize your pins": fija `applied-ai-engineering`, el TFG y el PSO.
2. **LinkedIn (15 min).** En "Acerca de" escribe 3 frases: quién eres, qué construyes y qué buscas (AI Engineer / FDE, Madrid, septiembre 2027). En "Destacado", añade el CLI.
3. **2 mensajes a antiguos alumnos de IE (20 min)** que trabajen en empresas de tus olas 2 o 3. Usa el mensaje base de tu doc privado y personaliza la primera frase con algo de su perfil.

---

### Domingo 10 · 15 min · Cierre

1. En `projects/02-docuchat/README.md` (créalo si no existe) añade una sección **Evaluation** con tus tres números y la fecha.
2. Log semanal. Mañana empieza el term 2: vuelves a 4–5 h/semana.
3. En Claude Code:
    ```
    Cerramos la semana 11. Revisa el checklist de resources/semanas/semana-11.md,
    ejecuta los tests de projects/02-docuchat y dime qué falta. Luego commit,
    push de semana11-docuchat-ask, PR, mergea y deja main al día.
    ```

---

📦 **Entregable:** DocuChat v0 con `/ask` citado, golden set de 30 preguntas y primer resultado de eval en el README.

✅ **Checklist**
- [ ] Las respuestas citan fragmentos y la página es correcta
- [ ] Dice "No lo encuentro en los documentos" en las trampas
- [ ] Golden set de 30 preguntas (5 trampas), sin PDFs en el repo
- [ ] hit@5 y abstención medidos y guardados por fecha
- [ ] Fallos clasificados en búsqueda, generación o golden set
- [ ] 9 tests en verde
- [ ] Perfil de GitHub, LinkedIn y 2 mensajes

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| Responde bien pero nunca cita | Refuerza la regla 2 del prompt con un ejemplo de respuesta citada (few-shot). |
| Se abstiene demasiado | Mira si la página buena estaba en el top 5. Si estaba, el prompt es demasiado estricto; si no, es un problema de búsqueda. |
| Se inventa respuestas en las trampas | Baja la temperatura a 0 y repite la regla 3 al final del mensaje de usuario. |
| `ModuleNotFoundError: app` en `run_eval.py` | Ejecútalo desde `projects/02-docuchat`: `uv run python evals/run_eval.py`. |
| hit@5 muy bajo (< 50 %) | Revisa primero tu golden set: ¿las páginas esperadas coinciden con la numeración del PDF (1 = primera página)? |
