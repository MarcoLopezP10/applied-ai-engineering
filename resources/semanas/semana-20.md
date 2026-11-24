# Semana 20 · 8–14 mar · Frontend (2/2): chat con citas y publicación

[← Semana 19](semana-19.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 21 →](semana-21.md)

🎯 **Objetivo:** DocuChat usable por cualquiera desde el navegador: preguntas, respuesta con citas clicables que enseñan el fragmento y su página, y la web publicada en Vercel conectada a tu API de AWS.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 9 | 1 h | Técnico | Componente de chat |
| Miércoles 10 | 1 h | Algoritmos + certificación | Repetir 3 fallados (30 min) + preguntas oficiales de Cloud Practitioner (30 min) |
| Jueves 11 | 1 h | Técnico | Citas clicables (la parte la escribes tú) |
| Sábado 13 | 1,5 h | Técnico + carrera | Publicar en Vercel (30 min) + 1 candidatura (1 h) |
| Domingo 14 | 15 min | Cierre | Log y PR |

Material de apoyo: roadmap técnico, semana 34 (frontend y despliegue).

---

### 📖 Qué vas a aprender

**Estado de una conversación.** El chat es una lista de turnos (pregunta + respuesta, o error) guardada en estado. Cada vez que preguntas, añades un turno "pendiente" y lo completas cuando llega la respuesta. Así la interfaz nunca se queda congelada.

**Convertir texto en interfaz.** El modelo devuelve "La 3FN elimina dependencias transitivas [2]". Tu código parte ese texto en trozos (texto normal y números de cita) y convierte cada `[2]` en un botón. Es una función pura y fácil de probar, la clase de tarea que piden en las pruebas técnicas de frontend.

**Variables de entorno en el frontend.** La URL de la API cambia entre tu ordenador y producción. En Vite se usan variables que empiezan por `VITE_`. Ojo: **todo lo que va al frontend es público**; nunca pongas ahí una clave secreta.

**Por qué las citas muestran el fragmento y no el PDF.** DocuChat no guarda los PDFs, solo sus fragmentos. Enseñar el fragmento con su página es suficiente para comprobar la respuesta. Guardar los archivos (en S3) sería la siguiente mejora.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana20-chat-web
```

Arranca la API (`uv run uvicorn app.main:app --reload`) y el frontend (`npm run dev` en `frontend/`).

---

### Martes 9 · 1 h · El chat

Crea `frontend/src/components/Chat.tsx`:

```tsx
import { useState } from "react";
import { crearCliente } from "../api/client";
import type { components } from "../api/schema";
import Respuesta from "./Respuesta";

type AskResponse = components["schemas"]["AskResponse"];
type Turno = { pregunta: string; respuesta?: AskResponse; error?: string };
type Props = { apiKey: string; onNoAutorizado: () => void };

export default function Chat({ apiKey, onNoAutorizado }: Props) {
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [pregunta, setPregunta] = useState("");
  const [esperando, setEsperando] = useState(false);

  async function preguntar() {
    const texto = pregunta.trim();
    if (!texto) return;
    setPregunta("");
    setEsperando(true);
    setTurnos((t) => [...t, { pregunta: texto }]); // turno pendiente
    const { data, error, response } = await crearCliente(apiKey).POST("/ask", {
      body: { question: texto, k: 5 },
    });
    if (response.status === 401) return onNoAutorizado();
    setTurnos((t) => {
      const copia = [...t];
      copia[copia.length - 1] = data
        ? { pregunta: texto, respuesta: data }
        : { pregunta: texto, error: (error as { detail?: string })?.detail ?? "Error" };
      return copia;
    });
    setEsperando(false);
  }

  return (
    <section className="tarjeta">
      <h2>Pregunta a tus documentos</h2>
      {turnos.map((t, i) => (
        <div key={i} className="turno">
          <p><strong>Tú:</strong> {t.pregunta}</p>
          {t.respuesta && <Respuesta datos={t.respuesta} />}
          {t.error && <p className="error">{t.error}</p>}
          {!t.respuesta && !t.error && <p className="muted">Buscando en tus documentos…</p>}
        </div>
      ))}
      <form onSubmit={(e) => { e.preventDefault(); preguntar(); }}>
        <input
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="Ej.: ¿Qué es la tercera forma normal?"
          disabled={esperando}
        />
        <button type="submit" disabled={esperando}>Preguntar</button>
      </form>
    </section>
  );
}
```

Crea también una versión provisional de `components/Respuesta.tsx`, que el jueves mejorarás:

```tsx
import type { components } from "../api/schema";

type AskResponse = components["schemas"]["AskResponse"];

export default function Respuesta({ datos }: { datos: AskResponse }) {
  return <p>{datos.answer}</p>;
}
```

En `App.tsx`, añade `<Chat apiKey={apiKey} onNoAutorizado={salir} />` debajo de `<Documentos … />` (con su `import`).

**Está bien si** puedes preguntar desde la web, ves "Buscando…" mientras espera y luego la respuesta, con los `[1]` como texto normal.

```bash
git add -A && git commit -m "DocuChat web: chat"
```

---

### Miércoles 10 · 1 h · Repaso y certificación

1. **Algoritmos (30 min).** En `practice/algoritmos/README.md`, elige 3 problemas con "¿Solo? = no". Repítelos sin mirar, en archivos nuevos (`*_v2.py`).
2. **Cloud Practitioner (30 min).** En [AWS Skill Builder](https://skillbuilder.aws), busca *AWS Certified Cloud Practitioner Official Practice Question Set* (20 preguntas, gratis). Hazlo con tiempo y apunta tu porcentaje y los temas en los que fallas. El examen es la semana que viene.

---

### Jueves 11 · 1 h · Citas clicables

**Paso 1 · Partir el texto: lo escribes tú (25 min).** Crea `frontend/src/citas.ts`:

```ts
// "Hola [1] y adiós [2][3]" → ["Hola ", 1, " y adiós ", 2, 3]
// Los textos quedan como string y las citas como number.
export function partirCitas(texto: string): Array<string | number> {
  // TODO: recorre el texto con la expresión /\[(\d+)\]/g
  //  - el texto entre citas va como string (sin añadir strings vacíos)
  //  - cada cita va como number
}
```

Para probarlo sin montar tests de frontend, escribe un pequeño script de comprobación, `frontend/src/citas.check.ts`:

```ts
import { partirCitas } from "./citas";

const casos: Array<[string, Array<string | number>]> = [
  ["Hola [1] y adiós [2][3]", ["Hola ", 1, " y adiós ", 2, 3]],
  ["Sin citas", ["Sin citas"]],
  ["[4] al principio", [4, " al principio"]],
];
for (const [entrada, esperado] of casos) {
  const real = JSON.stringify(partirCitas(entrada));
  console.log(real === JSON.stringify(esperado) ? "OK  " : "MAL ", entrada, real);
}
```

```bash
npx tsx src/citas.check.ts
```

<details>
<summary>Solución</summary>

```ts
export function partirCitas(texto: string): Array<string | number> {
  const partes: Array<string | number> = [];
  let ultimo = 0;
  for (const m of texto.matchAll(/\[(\d+)\]/g)) {
    const inicio = m.index ?? 0;
    if (inicio > ultimo) partes.push(texto.slice(ultimo, inicio));
    partes.push(Number(m[1]));
    ultimo = inicio + m[0].length;
  }
  if (ultimo < texto.length) partes.push(texto.slice(ultimo));
  return partes;
}
```
</details>

**Paso 2 · Usarlo en la respuesta (30 min).** Sustituye `components/Respuesta.tsx`:

```tsx
import { useState } from "react";
import type { components } from "../api/schema";
import { partirCitas } from "../citas";

type AskResponse = components["schemas"]["AskResponse"];
type Fragmento = components["schemas"]["Fragmento"];

export default function Respuesta({ datos }: { datos: AskResponse }) {
  const [abierto, setAbierto] = useState<Fragmento | null>(null);
  const porNumero = new Map(datos.retrieved.map((f) => [f.n, f]));
  const noEncontrado = datos.answer.startsWith("No lo encuentro");

  return (
    <div className={noEncontrado ? "respuesta aviso" : "respuesta"}>
      <p>
        {partirCitas(datos.answer).map((parte, i) =>
          typeof parte === "number" && porNumero.has(parte) ? (
            <button key={i} className="cita" onClick={() => setAbierto(porNumero.get(parte)!)}>
              {parte}
            </button>
          ) : (
            <span key={i}>{parte}</span>
          )
        )}
      </p>
      {abierto && (
        <blockquote className="fuente">
          <p className="muted">{abierto.document} · página {abierto.page}</p>
          <p>{abierto.text}</p>
          <button onClick={() => setAbierto(null)}>Cerrar</button>
        </blockquote>
      )}
    </div>
  );
}
```

Añade a `index.css`:

```css
.cita { padding: 0 6px; margin: 0 2px; font-size: 12px; border-radius: 10px; vertical-align: super; }
.fuente { background: #f6f8fa; border-left: 3px solid #1f6feb; margin: 8px 0; padding: 8px 12px; }
.aviso { color: #9a6700; }
.turno { border-top: 1px solid #d0d7de; padding-top: 8px; }
```

**Está bien si** al pulsar una cita se abre el fragmento con su documento y página, y una respuesta "No lo encuentro…" sale en color de aviso.

```bash
git add -A && git commit -m "DocuChat web: citas clicables con el fragmento de origen"
```

---

### Sábado 13 · 1,5 h

**Técnico, 30 min · Publicar en Vercel.**

1. En vercel.com → *Add New Project* → importa `applied-ai-engineering`.
2. **Root Directory:** `projects/02-docuchat/frontend`. Framework: Vite (lo detecta solo).
3. **Environment Variables:** `VITE_API_URL = https://docuchat-marco.duckdns.org` (tu dominio).
4. Deploy. Copia la URL que te da Vercel.
5. **Permitir esa web en la API.** En el servidor, añade al `.env`:

    ```
    CORS_ORIGINS=["https://tu-proyecto.vercel.app","http://localhost:5173"]
    ```

    y reinicia: `cd ~/docuchat && docker compose up -d api`.

**Está bien si** abres la URL de Vercel en el móvil, entras con tu clave y puedes subir un PDF y preguntar.

**Carrera, 1 h · 1 candidatura.** Desde hoy, en todas las candidaturas pon el enlace a la **demo en vivo**, no solo al repo.

---

### Domingo 14 · 15 min · Cierre

1. En el README de DocuChat, pon arriba del todo la línea **Live demo:** con la URL de Vercel (avisa de que hace falta clave y que la pidan por LinkedIn) y una captura de la pantalla de chat (`docs/chat.png`).
2. Log semanal.
3. PR y merge con Claude Code, como siempre.

---

✅ **Checklist**
- [ ] Chat con estado de "buscando" y errores visibles
- [ ] `partirCitas` pasa los 3 casos
- [ ] Citas clicables que enseñan fragmento, documento y página
- [ ] Web publicada en Vercel y funcionando contra AWS
- [ ] Demo y captura en el README
- [ ] 3 problemas repetidos, preguntas oficiales de Cloud Practitioner y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| En Vercel funciona la web pero las preguntas fallan con CORS | Falta la URL exacta de Vercel en `CORS_ORIGINS` (sin `/` al final) o no reiniciaste la API. |
| `CORS_ORIGINS` no se aplica | Tiene que ser JSON válido, con corchetes y comillas dobles. |
| `npx tsx` no existe | `npm install -D tsx`. |
| El botón de cita no hace nada | El número citado no está entre los recuperados (el modelo citó un `[7]` con 5 fragmentos). Es correcto que no haga nada. |
| Vercel compila pero la web sale en blanco | Abre la consola del navegador: casi siempre es `VITE_API_URL` sin definir. Las variables se aplican en el siguiente deploy. |
