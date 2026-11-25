# Semana 19 · 1–7 mar · Frontend en React + TypeScript (1/2)

[← Semana 18](semana-18.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 20 →](semana-20.md)

🎯 **Objetivo:** una interfaz web propia para DocuChat: entrar con tu clave, subir PDFs y ver tu lista de documentos. React y TypeScript aparecen en la mitad de las ofertas de FDE y de Software Engineer de tu análisis.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 2 | 1 h | Técnico | Preparar la API (CORS y tipos) y crear el proyecto React |
| Miércoles 3 | 1 h | Algoritmos | Kth Largest Element in a Stream y Last Stone Weight |
| Jueves 4 | 1 h | Técnico | Cliente tipado, pantalla de acceso y estructura |
| Sábado 6 | 1,5 h | Técnico + carrera | Subida y lista de documentos (30 min) + 1 candidatura (1 h) |
| Domingo 7 | 15 min | Cierre | Log y PR |

---

### 📖 Qué vas a aprender

**React en 5 ideas:**

1. Una interfaz es un árbol de **componentes**: funciones que devuelven HTML (JSX).
2. Un componente recibe datos de su padre por **props** (como argumentos de una función).
3. Lo que cambia con el tiempo (lo escrito en un input, la lista de documentos) va en **estado** con `useState`. Al cambiar el estado, React vuelve a pintar el componente.
4. Lo que hay que hacer al aparecer en pantalla (cargar la lista de la API) va en `useEffect`.
5. Los datos van de arriba abajo (props) y los avisos de abajo arriba (funciones que el padre pasa al hijo, como `onLogin`).

**TypeScript.** Es JavaScript con tipos. El editor te avisa si usas un campo que no existe, igual que hacen Pydantic y los *type hints* en Python.

**Tipos generados desde la API.** FastAPI publica su contrato en `/openapi.json`. Con `openapi-typescript` generas los tipos de TypeScript a partir de él: si cambias la API, regeneras y el frontend te marca lo que se ha roto. Para eso, la API tiene que declarar qué devuelve (`response_model`).

**CORS.** Por seguridad, el navegador no deja que una web en `localhost:5173` llame a una API en `localhost:8000` salvo que la API lo permita expresamente.

Para leer con calma esta semana: [react.dev → Quick Start](https://react.dev/learn) y "Thinking in React".

---

### Martes 2 · 1 h · API lista para el frontend y proyecto React

**Paso 1 · Node (5 min):**

```bash
brew install node
node --version   # 20 o superior
```

**Paso 2 · CORS (10 min).** En `Settings`:

~~~python
    cors_origins: list[str] = ["http://localhost:5173"]
~~~

En `app/main.py`, justo después de crear `app`:

~~~python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
~~~

**Paso 3 · Declarar qué devuelve cada endpoint (20 min).** Crea `app/schemas.py`:

~~~python
"""Formas de las respuestas de la API (se publican en /openapi.json)."""
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: int
    filename: str
    pages: int
    chunks: int


class Fragmento(BaseModel):
    n: int | None = None
    document: str
    page: int
    text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Fragmento]
    retrieved: list[Fragmento]
    latency_s: float | None = None
~~~

Y en `app/main.py`, importa los modelos y cambia **la línea del decorador** de cada endpoint (la función de debajo no cambia):

~~~python
from app.schemas import AskResponse, DocumentOut, Fragmento

# subir_documento:
@app.post("/documents", response_model=DocumentOut)
# listar_documentos:
@app.get("/documents", response_model=list[DocumentOut])
# search:
@app.get("/search", response_model=list[Fragmento])
# ask:
@app.post("/ask", response_model=AskResponse)
~~~

Comprueba en http://localhost:8000/docs que, al final de la página, aparecen los *Schemas* con esos nombres.

**Paso 4 · Proyecto React (25 min):**

```bash
cd projects/02-docuchat
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install openapi-fetch
npm install -D openapi-typescript
```

En `frontend/package.json`, dentro de `"scripts"`, añade:

```json
"gen:api": "openapi-typescript http://localhost:8000/openapi.json -o src/api/schema.d.ts"
```

Con la API arrancada en otra terminal:

```bash
mkdir -p src/api
npm run gen:api
npm run dev
```

**Está bien si** se abre http://localhost:5173 con la página de ejemplo de Vite y existe `src/api/schema.d.ts`. Ábrelo y busca `DocumentOut`: son tus tipos.

```bash
git add -A && git commit -m "DocuChat: CORS, respuestas tipadas y proyecto React"
```

---

### Miércoles 3 · 1 h · Algoritmos (Heap)

En Python, el montículo está en `heapq` y es de **mínimos**: `heap[0]` es siempre el menor.

**Kth Largest Element in a Stream** (Easy) → `practice/algoritmos/kth_largest_stream.py`

~~~python
import heapq


class KthLargest:
    def __init__(self, k: int, nums: list[int]):
        ...

    def add(self, val: int) -> int:
        ...


if __name__ == "__main__":
    kth = KthLargest(3, [4, 5, 8, 2])
    assert [kth.add(v) for v in [3, 5, 10, 9, 4]] == [4, 5, 5, 8, 8]
    print("OK")
~~~

<details>
<summary>Pista</summary>
Mantén un montículo de mínimos con solo los k más grandes. El k-ésimo mayor es entonces el más pequeño de ellos: heap[0].
</details>

**Last Stone Weight** (Easy) → `practice/algoritmos/last_stone_weight.py`

~~~python
def last_stone_weight(stones: list[int]) -> int:
    ...


if __name__ == "__main__":
    assert last_stone_weight([2, 7, 4, 1, 8, 1]) == 1
    assert last_stone_weight([1]) == 1
    print("OK")
~~~

<details>
<summary>Pista</summary>
Necesitas sacar siempre los dos mayores, pero heapq es de mínimos: guarda los números en negativo.
</details>

---

### Jueves 4 · 1 h · Cliente, acceso y estructura

Todo dentro de `projects/02-docuchat/frontend/src/`.

**Paso 1 · Cliente de la API (10 min).** `api/client.ts`:

```ts
import createClient from "openapi-fetch";
import type { paths } from "./schema";

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Cliente tipado: el editor sabe qué rutas existen y qué devuelven
export function crearCliente(apiKey: string) {
  return createClient<paths>({ baseUrl: API_URL, headers: { "X-API-Key": apiKey } });
}

// La subida de archivos va con FormData y fetch normal
export async function subirPdf(apiKey: string, archivo: File) {
  const form = new FormData();
  form.append("file", archivo);
  const r = await fetch(`${API_URL}/documents`, {
    method: "POST",
    headers: { "X-API-Key": apiKey },
    body: form,
  });
  if (!r.ok) throw new Error((await r.json()).detail ?? "Error al subir el PDF");
  return r.json();
}
```

**Paso 2 · Pantalla de acceso (15 min).** `components/Login.tsx`:

```tsx
import { useState } from "react";

type Props = { onLogin: (apiKey: string) => void };

export default function Login({ onLogin }: Props) {
  const [clave, setClave] = useState("");

  return (
    <main className="login">
      <h1>DocuChat</h1>
      <p>Pregunta a tus apuntes y recibe respuestas con la página de origen.</p>
      <form
        onSubmit={(e) => {
          e.preventDefault(); // evita que el navegador recargue la página
          if (clave.trim()) onLogin(clave.trim());
        }}
      >
        <input
          type="password"
          placeholder="Tu clave de acceso"
          value={clave}
          onChange={(e) => setClave(e.target.value)}
        />
        <button type="submit">Entrar</button>
      </form>
    </main>
  );
}
```

**Paso 3 · La app (15 min).** Sustituye `App.tsx`:

```tsx
import { useState } from "react";
import Login from "./components/Login";
import Documentos from "./components/Documentos";

export default function App() {
  // la clave se guarda en el navegador para no pedirla cada vez
  const [apiKey, setApiKey] = useState<string | null>(() => localStorage.getItem("apiKey"));

  if (!apiKey) {
    return <Login onLogin={(k) => { localStorage.setItem("apiKey", k); setApiKey(k); }} />;
  }

  const salir = () => { localStorage.removeItem("apiKey"); setApiKey(null); };

  return (
    <main className="app">
      <header>
        <h1>DocuChat</h1>
        <button onClick={salir}>Salir</button>
      </header>
      <Documentos apiKey={apiKey} onNoAutorizado={salir} />
    </main>
  );
}
```

**Paso 4 · Estilos mínimos (20 min).** Sustituye el contenido de `index.css` y borra `App.css`:

```css
:root { font-family: system-ui, sans-serif; color: #1f2328; background: #f6f8fa; }
body { margin: 0; }
.app, .login { max-width: 860px; margin: 0 auto; padding: 24px; }
header { display: flex; justify-content: space-between; align-items: center; }
form { display: flex; gap: 8px; margin: 16px 0; }
input { flex: 1; padding: 10px; border: 1px solid #d0d7de; border-radius: 8px; font-size: 15px; }
button { padding: 10px 16px; border: 0; border-radius: 8px; background: #1f6feb; color: white; cursor: pointer; }
button:disabled { opacity: 0.5; cursor: default; }
.tarjeta { background: white; border: 1px solid #d0d7de; border-radius: 8px; padding: 16px; margin: 12px 0; }
.error { color: #cf222e; }
.muted { color: #656d76; font-size: 14px; }
```

Todavía no compila, porque falta `Documentos`: es el sábado.

---

### Sábado 6 · 1,5 h

**Técnico, 30 min · Documentos: subida y lista.** Crea `components/Documentos.tsx`. La carga de la lista está hecha; la función `alSubir` la escribes tú:

```tsx
import { useEffect, useState } from "react";
import { crearCliente, subirPdf } from "../api/client";
import type { components } from "../api/schema";

type Documento = components["schemas"]["DocumentOut"];
type Props = { apiKey: string; onNoAutorizado: () => void };

export default function Documentos({ apiKey, onNoAutorizado }: Props) {
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    const { data, response } = await crearCliente(apiKey).GET("/documents");
    if (response.status === 401) return onNoAutorizado();
    setDocumentos(data ?? []);
  }

  useEffect(() => { cargar(); }, []); // al aparecer en pantalla

  async function alSubir(archivo: File) {
    // TODO:
    // 1. setSubiendo(true) y setError(null)
    // 2. await subirPdf(apiKey, archivo) dentro de try/catch
    //    - si falla: setError(el mensaje del error)
    // 3. en cualquier caso (finally): setSubiendo(false)
    // 4. si ha ido bien: await cargar() para refrescar la lista
  }

  return (
    <section>
      <div className="tarjeta">
        <h2>Tus documentos</h2>
        <input
          type="file"
          accept="application/pdf"
          disabled={subiendo}
          onChange={(e) => e.target.files?.[0] && alSubir(e.target.files[0])}
        />
        {subiendo && <p className="muted">Procesando el PDF… puede tardar un minuto.</p>}
        {error && <p className="error">{error}</p>}
        <ul>
          {documentos.map((d) => (
            <li key={d.id}>
              {d.filename} <span className="muted">· {d.pages} págs. · {d.chunks} fragmentos</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
```

<details>
<summary>Solución de alSubir</summary>

```tsx
  async function alSubir(archivo: File) {
    setSubiendo(true);
    setError(null);
    try {
      await subirPdf(apiKey, archivo);
      await cargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setSubiendo(false);
    }
  }
```
</details>

Prueba con la API en local (`uv run uvicorn app.main:app --reload`) y `npm run dev`:

1. Entra con tu clave → ves tus documentos.
2. Sube un PDF → aparece "Procesando…" y luego sale en la lista.
3. Sube un archivo de más de 20 MB → sale el error de la API en rojo.
4. Entra con una clave falsa → vuelves a la pantalla de acceso.

**Carrera, 1 h · 1 candidatura.** Si es de FDE o Software Engineer, ya puedes poner "React + TypeScript (learning, used in DocuChat)" en skills.

---

### Domingo 7 · 15 min · Cierre

1. Asegúrate de que `frontend/node_modules` no se sube: el `.gitignore` que crea Vite ya lo excluye; compruébalo con `git status`.
2. Log semanal.
3. En Claude Code:
    ```
    Cerramos la semana 19. Revisa el checklist de resources/semanas/semana-19.md,
    ejecuta npm run build en projects/02-docuchat/frontend y los tests de la API,
    y dime qué falta. Luego commit, push, PR, mergea y deja main al día.
    ```

---

✅ **Checklist**
- [ ] CORS configurado y `response_model` en todos los endpoints
- [ ] Tipos generados desde `/openapi.json`
- [ ] Entrar con la clave, ver la lista y subir un PDF desde el navegador
- [ ] Errores de la API visibles y clave inválida → vuelta al acceso
- [ ] Sé explicar componente, props, estado y efecto
- [ ] 2 problemas de heaps y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| En la consola del navegador: `blocked by CORS policy` | El origen de la web no está en `cors_origins` o la API no se ha reiniciado. |
| `npm run gen:api` falla | La API tiene que estar arrancada en el puerto 8000. |
| `Cannot find module './schema'` | Falta generar los tipos (`npm run gen:api`). |
| La lista se carga dos veces | Normal en desarrollo: React (StrictMode) ejecuta los efectos dos veces a propósito. En producción, una. |
| Un tipo sale como `unknown` | Ese endpoint no tiene `response_model`. Añádelo y regenera los tipos. |
