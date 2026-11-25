# Semana 17 · 15–21 feb · Despliegue en AWS

[← Semana 16](semana-16.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 18 →](semana-18.md)

🎯 **Objetivo:** DocuChat en Internet, con HTTPS y en tu propio dominio gratuito, por pocos euros al mes y con una alerta antes de gastar de más. Esta semana lo haces **a mano** para entender cada pieza; la que viene lo automatizas.

> Es la semana más pesada del term. Si el sábado no te da para la EC2, pásala al martes de la semana 18 y acorta allí el CI/CD.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 16 | 1 h | Técnico | Cuenta de AWS segura, presupuesto y base de datos en Supabase |
| Miércoles 17 | 1 h | Algoritmos | Same Tree y Subtree of Another Tree |
| Jueves 18 | 1 h | Técnico | Imagen Docker de DocuChat y subida a ECR |
| Sábado 20 | 1,5 h | Técnico + carrera | Servidor EC2, dominio y HTTPS (1 h) + 1 candidatura (30 min) |
| Domingo 21 | 15 min | Cierre | Comprobar desde fuera, README y PR |

Material de apoyo: roadmap técnico, semana 31 (AWS).

---

### 📖 Qué vas a aprender

La arquitectura que vas a montar:

```
Navegador ──HTTPS──▶ Caddy (certificado automático) ──▶ API DocuChat (contenedor)
                         │  EC2: un servidor Linux en AWS        │
                         └───────────────────────────────────────┘
                                                                  ├──▶ Supabase (Postgres + pgvector)
                                                                  ├──▶ Gemini (LLM y embeddings)
                                                                  └──▶ Langfuse (trazas)
Imagen Docker: tu Mac ──push──▶ ECR (registro de imágenes de AWS) ──pull──▶ EC2
```

- **EC2:** un ordenador virtual en AWS que pagas por horas.
- **ECR:** un "GitHub de imágenes Docker". Subes la imagen y el servidor la descarga.
- **IAM:** quién puede hacer qué. Nunca se usa el usuario raíz (*root*) para el día a día, y el servidor tiene un **rol** con permiso solo para descargar imágenes, sin contraseñas guardadas.
- **Security group:** el cortafuegos del servidor. Solo abres SSH (para tu IP) y 80/443 (web).
- **Supabase para la base de datos:** es Postgres con pgvector, tiene capa gratuita y ya lo conoces del TFG. Montar Postgres en la misma EC2 también funciona, pero en una máquina pequeña se queda sin memoria.
- **Caddy:** servidor web que pide y renueva solo el certificado HTTPS. Para eso necesita un **dominio**: usarás uno gratuito de DuckDNS.

---

### Martes 16 · 1 h · Cuenta, presupuesto y base de datos

**Paso 1 · Cuenta de AWS segura (20 min).**

1. Crea la cuenta en aws.amazon.com. Revisa las condiciones de la capa gratuita al darte de alta: desde 2025 funciona con créditos durante unos meses.
2. **Activa MFA en el usuario raíz:** menú de la cuenta → Security credentials → Assign MFA, con una app de autenticación.
3. **Antes de crear nada más:** Billing → **Budgets** → Create budget → *Monthly cost budget* de **10 USD**, con aviso por correo al 80 %.
4. IAM → Users → Create user `marco-cli`. Dale los permisos `AmazonEC2ContainerRegistryPowerUser` y `AmazonEC2FullAccess`. Luego Security credentials → Create access key (tipo CLI) y guarda las dos claves en tu gestor de contraseñas.
5. En tu Mac:

    ```bash
    brew install awscli
    aws configure   # pega las dos claves; región eu-south-2 (España) o eu-west-1 (Irlanda)
    aws sts get-caller-identity   # debe mostrar el usuario marco-cli
    ```

**Paso 2 · Base de datos en Supabase (30 min).**

1. En supabase.com crea un proyecto `docuchat`, con región en la UE y una contraseña fuerte.
2. Project Settings → Database → *Connection string* → **Session pooler**. Copia la URI y cambia el principio `postgresql://` por `postgresql+psycopg://`.
3. Carga tus PDFs en esa base de datos desde tu Mac. `init_db` crea la extensión y las tablas:

    ```bash
    cd projects/02-docuchat
    DATABASE_URL="postgresql+psycopg://postgres.xxxx:CONTRASEÑA@aws-0-eu-....pooler.supabase.com:5432/postgres" \
      uv run python scripts/ingestar_carpeta.py
    ```

4. **Está bien si** en Supabase → Table Editor ves `documents` y `chunks` con datos.

> El plan gratuito de Supabase pausa el proyecto tras una semana sin actividad. Si lo encuentras pausado, se reactiva con un clic.

**Paso 3 · Guarda la URL** en tu gestor de contraseñas. Nunca va al repo.

---

### Miércoles 17 · 1 h · Algoritmos

Usa `TreeNode` y `desde_lista` de la semana 16.

**Same Tree** (Easy) → `practice/algoritmos/same_tree.py`

~~~python
def is_same_tree(p, q) -> bool:
    ...


if __name__ == "__main__":
    assert is_same_tree(desde_lista([1, 2, 3]), desde_lista([1, 2, 3])) is True
    assert is_same_tree(desde_lista([1, 2]), desde_lista([1, None, 2])) is False
    print("OK")
~~~

**Subtree of Another Tree** (Easy) → `practice/algoritmos/subtree.py`

~~~python
def is_subtree(root, sub_root) -> bool:
    ...


if __name__ == "__main__":
    assert is_subtree(desde_lista([3, 4, 5, 1, 2]), desde_lista([4, 1, 2])) is True
    assert is_subtree(desde_lista([3, 4, 5, 1, 2, None, None, None, None, 0]), desde_lista([4, 1, 2])) is False
    print("OK")
~~~

<details>
<summary>Pista</summary>
Subtree reutiliza Same Tree: para cada nodo del árbol grande, ¿es el mismo árbol que sub_root?
</details>

---

### Jueves 18 · 1 h · Imagen Docker y ECR

**Paso 1 · Dockerfile de DocuChat (25 min).** En `projects/02-docuchat/Dockerfile`:

```dockerfile
FROM python:3.11-slim

# uv, copiado de su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Dependencias primero (capa que se reutiliza si no cambian)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Después el código
COPY app ./app

EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Y `projects/02-docuchat/.dockerignore`, para no meter en la imagen lo que no debe ir:

```
.venv
.env
docs/pdfs
evals/results
__pycache__
tests
```

Pruébala en local con tu base de datos de Supabase:

```bash
docker build -t docuchat .
docker run --rm -p 8000:8000 --env-file ../../.env -e DATABASE_URL="(la de Supabase)" docuchat
curl -s -H "X-API-Key: TU_CLAVE" "localhost:8000/search?q=normal+form"
```

**Paso 2 · Subirla a ECR (25 min).**

1. Consola de AWS → ECR → Create repository → nombre `docuchat`, privado.
2. En la página del repositorio, pulsa **View push commands** y ejecuta los cuatro comandos que te da (login, build, tag y push). Tienen esta forma:

    ```bash
    aws ecr get-login-password --region eu-south-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.eu-south-2.amazonaws.com
    docker build -t docuchat .
    docker tag docuchat:latest 123456789012.dkr.ecr.eu-south-2.amazonaws.com/docuchat:latest
    docker push 123456789012.dkr.ecr.eu-south-2.amazonaws.com/docuchat:latest
    ```

**Está bien si** en ECR aparece la imagen con la etiqueta `latest`.

```bash
git add -A && git commit -m "DocuChat: Dockerfile para producción"
```

---

### Sábado 20 · 1,5 h

**Técnico, 1 h · Servidor, dominio y HTTPS.**

1. **Rol para el servidor (5 min).** IAM → Roles → Create role → *AWS service: EC2* → permiso `AmazonEC2ContainerRegistryReadOnly` → nombre `docuchat-ec2`.
2. **Lanzar la EC2 (10 min).** EC2 → Launch instance:
    - Nombre `docuchat`, imagen **Amazon Linux 2023**, tipo **t3.micro** (si se queda sin memoria, t3.small).
    - Key pair: crea `docuchat` y guarda el `.pem` en `~/.ssh/`.
    - Network settings: SSH solo desde *My IP*; marca *Allow HTTPS* y *Allow HTTP* desde Internet.
    - Advanced details → IAM instance profile: `docuchat-ec2`.
3. **Dominio gratuito (5 min).** En duckdns.org entra con GitHub, crea un subdominio (por ejemplo `docuchat-marco`) y pon la IP pública de tu EC2.
4. **Preparar el servidor (15 min):**

    ```bash
    chmod 400 ~/.ssh/docuchat.pem
    ssh -i ~/.ssh/docuchat.pem ec2-user@IP_PUBLICA
    ```

    Ya dentro del servidor:

    ```bash
    sudo dnf install -y docker
    sudo systemctl enable --now docker
    sudo usermod -aG docker ec2-user
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    exit
    ```

    Vuelve a entrar con `ssh` (para que se aplique el grupo `docker`) y comprueba `docker compose version`.
5. **Archivos del servidor (15 min).** En el servidor, `mkdir ~/docuchat && cd ~/docuchat`, y crea tres archivos con `nano`:

    `compose.yml`:

    ```yaml
    services:
      api:
        image: 123456789012.dkr.ecr.eu-south-2.amazonaws.com/docuchat:${IMAGE_TAG:-latest}
        env_file: .env
        restart: unless-stopped
      caddy:
        image: caddy:2
        ports:
          - "80:80"
          - "443:443"
        volumes:
          - ./Caddyfile:/etc/caddy/Caddyfile
          - caddy_data:/data
        restart: unless-stopped
    volumes:
      caddy_data:
    ```

    `Caddyfile` (cambia el dominio por el tuyo):

    ```
    docuchat-marco.duckdns.org {
        reverse_proxy api:8000
    }
    ```

    `.env` (después, `chmod 600 .env`):

    ```
    GOOGLE_API_KEY=...
    DATABASE_URL=postgresql+psycopg://...supabase...
    API_KEYS={"tu-clave":"marco"}
    LANGFUSE_PUBLIC_KEY=...
    LANGFUSE_SECRET_KEY=...
    LANGFUSE_HOST=https://cloud.langfuse.com
    ```

6. **Arrancar (10 min):**

    ```bash
    aws ecr get-login-password --region eu-south-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.eu-south-2.amazonaws.com
    docker compose up -d
    docker compose logs -f   # Ctrl+C para salir
    ```

**Está bien si** desde tu Mac `https://docuchat-marco.duckdns.org/health` devuelve `{"status":"ok"}` con el candado de HTTPS.

**Carrera, 30 min · 1 candidatura.**

---

### Domingo 21 · 15 min · Cierre

1. Desde tu Mac, haz una pregunta real a la URL pública:

    ```bash
    curl -s -X POST https://docuchat-marco.duckdns.org/ask \
      -H "X-API-Key: TU_CLAVE" -H "Content-Type: application/json" \
      -d '{"question": "What is a data warehouse?"}'
    ```

2. En el README de DocuChat, añade una sección **Deployment** con el diagrama de la arquitectura de arriba y el **coste mensual estimado**. Calcúlalo con la calculadora de AWS: EC2 t3.micro + IPv4 pública + ECR. Las IPv4 públicas se pagan aparte desde 2024.
3. Log semanal.
4. Commit, push de tu rama `semana17-aws` (créala si trabajaste en `main`), PR y merge, igual que siempre con Claude Code.

---

✅ **Checklist**
- [ ] MFA en el usuario raíz y presupuesto de 10 USD con aviso
- [ ] Usuario IAM para la CLI; el servidor usa un rol, no claves
- [ ] Base de datos en Supabase con tus documentos
- [ ] Imagen en ECR
- [ ] `https://…/health` responde con HTTPS
- [ ] Arquitectura y coste en el README
- [ ] 2 problemas de árboles y 1 candidatura

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `ssh: Connection timed out` | El security group no permite SSH desde tu IP (puede haber cambiado si estás en otra wifi). Edítalo y pon *My IP* otra vez. |
| `no basic auth credentials` al hacer pull | Falta el `docker login` de ECR en el servidor, o la EC2 no tiene el rol `docuchat-ec2`. |
| Caddy no consigue el certificado | DuckDNS no apunta a la IP actual, o los puertos 80/443 están cerrados en el security group. |
| La API se reinicia sin parar | `docker compose logs api`. Lo más habitual es una variable que falta en `.env` o una `DATABASE_URL` sin `+psycopg`. |
| El servidor se queda sin memoria | Pasa a t3.small, o añade un archivo de swap de 1 GB. |
| La IP cambia al parar y arrancar la EC2 | Normal. Actualiza DuckDNS, o asigna una Elastic IP (tiene coste mientras exista). |
