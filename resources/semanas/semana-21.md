# Semana 21 · 15–21 mar · Examen Cloud Practitioner + usuarios reales

[← Semana 20](semana-20.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 22 →](semana-22.md)

🎯 **Objetivo:** aprobar tu primera certificación de AWS y que 5 compañeros usen DocuChat con sus apuntes durante una semana. Usuarios reales y una métrica de uso valen más en una entrevista que cualquier funcionalidad nueva.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 16 | 1 h | Técnico | Preparar el acceso de 5 usuarios y su seguimiento |
| Miércoles 17 | 30 min | Algoritmos | 1 Easy de repaso |
| Jueves 18 (o el día de tu examen) | 1,5 h | Certificación | Examen AWS Certified Cloud Practitioner |
| Sábado 20 | 1 h | Carrera | 1 candidatura |
| Domingo 21 | 15 min | Cierre | Ver el uso en Langfuse, log y PR |

---

### 📖 Qué vas a aprender

**Probar con usuarios es otra cosa.** Tus 30 preguntas del golden set las escribiste tú. Tus compañeros preguntarán de formas que no se te han ocurrido, subirán PDFs raros y encontrarán fallos que tus tests no cubren. Eso es exactamente lo que vive un FDE con un cliente.

**Saber quién usa qué.** Si cada traza de Langfuse lleva el usuario, puedes contestar con datos: cuántas preguntas hizo cada uno, cuáles fallaron y cuánto costó.

**El examen Cloud Practitioner** mide conceptos, no práctica: modelo de responsabilidad compartida, precios, servicios principales (EC2, S3, RDS, Lambda, IAM…) y buenas prácticas. Has usado varios de verdad en las semanas 17–18, lo que ayuda mucho.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana21-usuarios
```

**Reserva el examen ya**, si no lo has hecho: con el voucher del máster, si lo hay (pendiente 6 de tu doc), o en aws.amazon.com/certification. Se puede hacer online (Pearson VUE, con webcam y la mesa despejada) o en un centro de Madrid.

---

### Martes 16 · 1 h · Preparar a los usuarios

**Paso 1 · Trazas con usuario (15 min).** En `app/generate.py`, pon arriba `from langfuse import get_client` y añade al principio de `responder`:

~~~python
    if owner:
        get_client().update_current_trace(user_id=owner)
~~~

Así, en Langfuse → Users, verás la actividad de cada uno. Despliega con un PR y merge (el CD lo sube solo).

**Paso 2 · Claves (10 min).** Genera 5 claves, una por persona:

```bash
for n in 1 2 3 4 5; do python3 -c "import secrets; print(secrets.token_urlsafe(24))"; done
```

En el `.env` del servidor, amplía `API_KEYS` con un nombre corto por persona:

```
API_KEYS={"tu-clave":"marco","clave1":"ana","clave2":"luis","clave3":"sara","clave4":"pablo","clave5":"irene"}
```

y reinicia: `cd ~/docuchat && docker compose up -d api`.

**Paso 3 · Formulario de feedback (15 min).** En Google Forms, crea 3 preguntas:

1. ¿Te ha sido útil para estudiar? (1–5)
2. ¿Qué ha fallado o qué te ha confundido? (texto)
3. ¿Lo seguirías usando? ¿Por qué? (texto)

**Paso 4 · Invitación (20 min).** Elige 5 compañeros que estén estudiando algo con PDFs del máster y mándales a cada uno, por privado, su clave:

> ¡Hola [nombre]! Estoy construyendo DocuChat, una web a la que le subes tus apuntes en PDF y te responde preguntas citando la página. ¿Me ayudas probándolo esta semana para estudiar?
>
> 🔗 [URL de Vercel]
> 🔑 Tu clave: [clave] (es solo tuya)
>
> Sube 1 o 2 PDFs de una asignatura y hazle las preguntas que te harías al estudiar. El domingo te paso un formulario de 3 preguntas (2 minutos). ¡Gracias!

---

### Miércoles 17 · 30 min · Algoritmos

Elige un Easy que hayas resuelto hace más de 3 semanas y repítelo sin mirar, en 15 minutos como máximo. Semana de examen: lo importante es no romper la racha.

---

### Jueves 18 (o el día de tu examen) · Examen

**La víspera (opcional, 30 min):** repasa los temas que fallaste en las preguntas oficiales de la semana 20. Lo que más suele salir:

- **Responsabilidad compartida:** AWS protege la nube (hardware, centros de datos); tú, lo que pones en ella (datos, IAM, configuración).
- **Modelos de precio:** On-Demand, Reserved/Savings Plans, Spot.
- **Herramientas de costes:** Budgets, Cost Explorer y Pricing Calculator. Ya las has usado.
- **Diferencias entre servicios parecidos:** EC2 frente a Lambda, RDS frente a DynamoDB, S3 frente a EBS.
- **Seguridad:** IAM, MFA, roles frente a claves. Lo hiciste en la semana 17.

**En el examen:** 90 minutos y 65 preguntas. Marca las dudosas y vuelve al final. No dejes ninguna en blanco: no restan.

**Después:** añade la certificación a LinkedIn (sección *Licenses & certifications*, con el enlace de Credly) y al CV.

---

### Sábado 20 · 1 h · Carrera

1 candidatura. Si ya tienes el aprobado, menciónalo: "AWS Certified Cloud Practitioner (March 2027)".

---

### Domingo 21 · 15 min · Cierre

1. **Mira el uso en Langfuse** (Users y Tracing): cuántas personas han entrado, cuántas preguntas en total, cuántas respuestas "No lo encuentro" y la latencia media. Apúntalo en `docs/notas.md`.
2. **Envía el formulario** a los 5 y recuérdaselo a quien no haya entrado todavía. La semana que viene trabajas con sus respuestas.
3. Log semanal.
4. PR y merge de la rama, como siempre.

---

✅ **Checklist**
- [ ] Las trazas de Langfuse llevan el usuario
- [ ] 5 usuarios con su clave y su invitación enviada
- [ ] Formulario de feedback creado y enviado
- [ ] Examen Cloud Practitioner hecho (y en LinkedIn y el CV si aprobaste)
- [ ] Uso de la semana apuntado
- [ ] 1 problema repetido y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| Un compañero dice "API key no válida" | Comprueba que la clave está en el JSON del `.env` del servidor sin espacios de más y que reiniciaste la API. |
| Alguien sube un PDF y tarda muchísimo | PDF muy largo: los embeddings tardan. Bájale el límite a 10 MB o avisa de que tenga paciencia. |
| Nadie lo usa en 3 días | Normal. Escríbeles otra vez con una pregunta concreta que podrían hacerle ("¿le preguntas por el tema 4 de Estadística?"). |
| No apruebas el examen | Pasa. Apunta los dominios con peor nota del informe, repasa 2 semanas y vuelve a presentarte. No cambia nada más del plan. |
