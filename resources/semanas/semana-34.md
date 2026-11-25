# Semana 34 · 14–20 jun · El capstone como caso de cliente

[← Semana 33](semana-33.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 35 →](semana-35.md)

🎯 **Objetivo:** convertir el capstone en tu **experiencia con cliente real**, contada en una página, y preparar el examen de AWS Data Engineer si viene con la optativa. Semana más ligera en lo técnico, porque es cuando más entrevistas suele haber.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 15 | 1 h | Técnico | Caso del capstone de una página |
| Miércoles 16 | 30 min | Algoritmos | 1 problema de repaso |
| Jueves 17 | 1,5 h | Certificación | Repaso de AWS Data Engineer (o CI/CD del agente) |
| Sábado 19 | 1–2 h | Carrera | Entrevistas en curso y candidaturas |
| Domingo 20 | 15 min | Cierre | Log |

---

### 📖 Por qué importa

En tu análisis de puestos, la **experiencia con cliente real** era el requisito casi universal de FDE, y el capstone es lo más parecido que tienes. Contado bien, responde a la pregunta "cuéntame una vez que trabajaste con un cliente" con una historia de verdad: un problema de negocio, unas personas, una entrega y un impacto.

---

### Martes 15 · 1 h · Caso del capstone

**Paso 1 · Qué se puede contar (10 min).** Pregunta a tu tutor o al contacto de la empresa: "¿Puedo describir el proyecto en mi portfolio sin datos confidenciales? ¿Puedo nombrar a la empresa?". Si no se puede nombrar, usa una descripción ("una cadena de retail española").

**Paso 2 · El caso (50 min).** Créalo en `case-studies/capstone.md` en la raíz del repo (o en tu doc privado si no se puede publicar):

```markdown
# [Nombre o descripción de la empresa]: [qué resolvisteis en 6 palabras]

**Contexto:** quién es el cliente y qué le dolía (2 frases).
**Mi papel:** qué hice yo dentro del equipo (no "el equipo hizo").
**Qué entregamos:** la solución en 3 líneas, con su stack.
**Cómo trabajamos con el cliente:** reuniones de descubrimiento, demos, cambios por su feedback.
**Impacto:** la métrica acordada al inicio (semana 24): antes → después, o la estimación con sus supuestos.
**Qué aprendí:** 2 cosas, una técnica y una de trato con cliente.
```

Escribe también la versión STAR de 2 minutos para entrevistas y súmala a tus historias.

---

### Miércoles 16 · 30 min · Algoritmos

1 problema de repaso. Semana de entrevistas: mantener el ritmo, nada más.

---

### Jueves 17 · 1,5 h · AWS Data Engineer (si viene con la optativa)

El examen DEA-C01 tiene 4 dominios. Repasa cada uno con lo que has visto en la optativa *Data Analytics in the Cloud*:

| Dominio | Peso aproximado | Servicios clave |
|---|:---:|---|
| Ingesta y transformación de datos | 34 % | Kinesis, Glue, Lambda, EMR, Step Functions |
| Gestión de almacenamiento | 26 % | S3 (clases y ciclo de vida), Redshift, DynamoDB, Lake Formation |
| Operación y soporte | 22 % | CloudWatch, Athena, orquestación y monitorización de pipelines |
| Seguridad y gobierno | 18 % | IAM, KMS, cifrado, Lake Formation, auditoría con CloudTrail |

1. Haz el *Official Practice Question Set* de DEA-C01 en AWS Skill Builder (gratis).
2. Apunta los 2 dominios con peor resultado y repasa solo esos.

**Si no vas a hacer el examen:** usa esta hora y media para el CI/CD del agente (copia `docuchat-deploy.yml` como `agent-deploy.yml`, como explica la semana 32).

---

### Sábado 19 · 1–2 h · Carrera

Es el pico de procesos de la ola 3. Prioridad:

1. **Preparar entrevistas concretas.** Para cada una: lee la oferta, elige qué proyecto contar (DocuChat para AI Engineer, el agente para FDE, el ML para ML Engineer), repasa el pitch y prepara 2 preguntas para ellos.
2. **Follow-ups** de candidaturas sin respuesta a los 10 días.
3. Si queda tiempo, 1 candidatura.

---

### Domingo 20 · 15 min · Cierre

Log semanal y commit del caso del capstone (si es público).

---

✅ **Checklist**
- [ ] Permiso para contar el capstone y caso de una página
- [ ] Historia STAR del capstone
- [ ] Repaso de DEA por dominios (o CI/CD del agente)
- [ ] Entrevistas preparadas y follow-ups hechos
