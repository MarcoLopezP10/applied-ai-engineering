# Semana 23 · 29 mar – 4 abr · Vídeo de DocuChat, proyecto de ML y cierre del term 2

[← Semana 22](semana-22.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 24 →](semana-24.md)

🎯 **Objetivo:** cerrar el term 2 con dos proyectos presentables: DocuChat (con vídeo) y un modelo de ML en producción a partir de tu trabajo de MLOps. Además, el CV actualizado y el capstone elegido.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 30 | 1 h | Técnico | Guion y grabación del vídeo de DocuChat |
| Miércoles 31 | 1 h | Algoritmos | Number of Islands |
| Jueves 1 | 1 h | Técnico | Publicar el proyecto de ML en producción |
| Sábado 3 | 1,5 h | Técnico + carrera | Completar el proyecto de ML (30 min) + CV y capstone (1 h) |
| Domingo 4 | 15 min | Cierre | Checkpoint del term 2, log y PR |

---

### 📖 Qué vas a aprender

**Un vídeo de 2 minutos** es lo que más ve un recruiter: casi nadie clona un repo, pero muchos le dan al play. Lo que importa es el guion, no la edición.

**ML en producción (para ML Engineer).** Tu análisis de puestos decía que la prueba que pide cualquier oferta de ML Engineer es "un modelo propio en producción": entrenado y registrado (MLflow), servido por una API, empaquetado en Docker y vigilado (*drift*). En el máster has hecho casi todo eso en MLOps. Esta semana lo conviertes en un proyecto público y presentable.

**Drift.** Un modelo entrenado con datos de 2025 empeora si los datos de 2027 cambian: otros clientes, otros precios. Vigilar si la distribución de los datos nuevos se parece a la del entrenamiento es la parte "Ops" de MLOps.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana23-video-ml
```

---

### Martes 30 · 1 h · Vídeo de DocuChat

**Paso 1 · Guion (20 min).** Escríbelo palabra por palabra, en inglés, y léelo en voz alta cronometrando:

| Tiempo | Qué se ve | Qué dices |
|---|---|---|
| 0:00–0:15 | Tu cara o la portada | El problema: "Lecture PDFs are long, and generic chatbots answer from memory, so you can't trust them." |
| 0:15–1:15 | La web: subir un PDF, 2 preguntas y abrir una cita; una pregunta trampa → "No lo encuentro" | Qué hace y por qué las citas importan |
| 1:15–1:45 | Tabla de métricas del write-up | "On a 30-question golden set: hit@5 X %, correctness Y/3. 5 classmates used it for a week." |
| 1:45–2:00 | El diagrama de arquitectura | Una decisión: "I tested sentence vs fixed chunking and kept X because…" |

**Paso 2 · Grabar (30 min).** Con Loom (gratis, hasta 5 minutos) o con QuickTime → Nueva grabación de pantalla. Sin edición: si te equivocas, vuelve a grabar. Ten 2 preguntas preparadas que sepas que salen bien.

**Paso 3 · Publicar (10 min).** Súbelo a YouTube como **oculto** (no listado) o deja el enlace de Loom. Ponlo arriba del README de DocuChat y en "Destacado" de LinkedIn.

---

### Miércoles 31 · 1 h · Algoritmos (Graphs)

**Number of Islands** (Medium) → `practice/algoritmos/number_of_islands.py`

~~~python
def num_islands(grid: list[list[str]]) -> int:
    ...


if __name__ == "__main__":
    grid = [
        ["1", "1", "0", "0", "0"],
        ["1", "1", "0", "0", "0"],
        ["0", "0", "1", "0", "0"],
        ["0", "0", "0", "1", "1"],
    ]
    assert num_islands(grid) == 3
    print("OK")
~~~

<details>
<summary>Pista</summary>
Recorre la cuadrícula. Cada vez que encuentres un "1" sin visitar, suma una isla y "húndela": marca como visitados todos los "1" conectados, con DFS o BFS.
</details>

---

### Jueves 1 · 1 h · Proyecto de ML en producción

> No sé exactamente qué modelo hiciste en MLOps; esta guía vale para cualquier modelo de scikit-learn. Antes de publicar: **permiso del profesor** y **solo datos públicos** (por ejemplo, de Kaggle o de UCI). Si los datos de clase no son públicos, reentrena el mismo pipeline con un dataset público parecido.

**Paso 1 · Estructura (15 min).** Copia tu trabajo a `projects/04-ml-en-produccion/` con esta forma:

```
04-ml-en-produccion/
├── data/              # o un script que lo descarga (no subas datasets grandes)
├── train.py           # entrena y registra en MLflow
├── api/main.py        # sirve el modelo
├── monitoring/        # informe de drift
├── Dockerfile
└── README.md
```

**Paso 2 · Entrenar y registrar (20 min).** Si tu `train.py` aún no usa MLflow, añade lo mínimo:

~~~python
import joblib
import mlflow
from sklearn.metrics import f1_score  # o la métrica de tu problema

mlflow.set_experiment("ml-en-produccion")
with mlflow.start_run():
    mlflow.log_params(modelo.get_params())
    modelo.fit(X_train, y_train)
    mlflow.log_metric("f1", f1_score(y_test, modelo.predict(X_test)))
    mlflow.sklearn.log_model(modelo, "model")
    joblib.dump(modelo, "api/model.joblib")  # copia para la API
~~~

Ejecuta `uv run mlflow ui`, abre http://localhost:5000 y haz una captura de los runs para el README.

**Paso 3 · La API (25 min).** `api/main.py`. Cambia los campos de `Entrada` por las variables de tu modelo:

~~~python
"""Sirve el modelo entrenado."""
import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ML en producción")
modelo = joblib.load("model.joblib")


class Entrada(BaseModel):
    # TODO: una línea por variable de entrada de tu modelo, con su tipo
    edad: int
    ingresos: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(entrada: Entrada):
    X = pd.DataFrame([entrada.model_dump()])
    return {"prediction": modelo.predict(X).tolist()[0]}
~~~

Pruébala con `cd api && uv run uvicorn main:app --reload` y `/docs`.

---

### Sábado 3 · 1,5 h

**Técnico, 30 min · Docker y drift.**

1. **Dockerfile:** el mismo patrón que DocuChat (semana 17), copiando `api/` y arrancando `uvicorn main:app`.
2. **Informe de drift** con [Evidently](https://docs.evidentlyai.com). Compara los datos de entrenamiento con los de test, como si fueran "datos nuevos":

    ~~~python
    # monitoring/drift.py · comprueba en la documentación de Evidently los imports de tu versión
    import pandas as pd
    from evidently import Report
    from evidently.presets import DataDriftPreset

    referencia = pd.read_csv("data/train.csv")
    actuales = pd.read_csv("data/test.csv")
    informe = Report([DataDriftPreset()])
    resultado = informe.run(reference_data=referencia, current_data=actuales)
    resultado.save_html("monitoring/drift_report.html")
    ~~~

3. **README** del proyecto con la plantilla de siempre: problema, datos, modelo y métrica, captura de MLflow, cómo llamar a la API, drift y qué mejorarías.

**Carrera, 1 h:**

1. **CV (30 min).** Añade DocuChat en proyectos, con números, en una o dos líneas. Por ejemplo:
    > *DocuChat — RAG over PDFs with cited answers (FastAPI, pgvector, React/TS, AWS, CI/CD). hit@5 of X % on a 30-question eval; used by 5 classmates.*

    Añade también la certificación de Cloud Practitioner. Mantén tu formato y una sola página.
2. **Capstone (30 min).** Si ya se puede elegir, elige un *corporate project*, mejor si es de IA o de datos con un cliente real: es tu experiencia de FDE. Si hay que escribir una motivación, menciona DocuChat como prueba de lo que sabes construir.

---

### Domingo 4 · 15 min · Cierre del term 2

1. **Checkpoint de fin de term 2:** compara con la tabla del roadmap (fin de S23: Cloud Practitioner, 5 usuarios, vídeo y proyecto 04; 34 problemas, 15 candidaturas y 8 contactos). Apúntalo en el log. Si vas por detrás, decide qué recortar del term 3: el alcance del agente, nunca candidaturas ni algoritmos.
2. Actualiza el README principal: proyecto 02 en **Done**, proyecto 04 en **Done**.
3. PR y merge.

---

✅ **Checklist**
- [ ] Vídeo de 2 minutos publicado y enlazado
- [ ] Proyecto 04 con MLflow, API, Docker, drift y README
- [ ] Permiso del profesor y datos públicos
- [ ] CV con DocuChat y la certificación
- [ ] Capstone elegido
- [ ] Number of Islands y checkpoint del term 2

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| El vídeo sale de 3 minutos | Recorta la demo a 2 preguntas y la parte de métricas a una sola frase. |
| La API dice que faltan columnas | El orden y los nombres de `Entrada` tienen que coincidir con las columnas con las que entrenaste. |
| Error de import con Evidently | Su API cambió en 2025. Mira el "Quickstart" de su documentación para tu versión. |
| `pickle`/`joblib` da error de versión | Entrena y sirve con la misma versión de scikit-learn: fíjala en `pyproject.toml`. |
