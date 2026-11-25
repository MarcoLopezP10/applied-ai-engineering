# Semana 18 · 22–28 feb · CI/CD: desplegar con cada merge

[← Semana 17](semana-17.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 19 →](semana-19.md)

🎯 **Objetivo:** que cada merge a `main` que toque DocuChat pase los tests, construya la imagen, la suba a ECR y actualice el servidor **sin que toques nada**. Y saber volver a la versión anterior si algo sale mal.

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Martes 23 | 1 h | Técnico | Workflow: tests → build → push a ECR |
| Miércoles 24 | 1 h | Algoritmos | Lowest Common Ancestor of a BST y Level Order Traversal |
| Jueves 25 | 1 h | Técnico | Desplegar en la EC2 con SSM y comprobar `/health` |
| Sábado 27 | 1,5 h | Técnico + carrera | Probar un rollback (30 min) + 1 candidatura y 1 mensaje (1 h) |
| Domingo 28 | 15 min | Cierre | Checkpoint de febrero, log y PR |

Material de apoyo: roadmap técnico, semana 32 (CI/CD).

---

### 📖 Qué vas a aprender

**CI/CD.** La *integración continua* (CI) ya la tienes: tests en cada push. El *despliegue continuo* (CD) añade que, si todo pasa en `main`, la nueva versión llega sola a producción. El flujo:

```
merge a main ─▶ tests + ruff ─▶ docker build ─▶ push a ECR (etiqueta = commit) ─▶ servidor: pull + up ─▶ /health
                    │ si falla, se para aquí y producción no se toca
```

**Etiquetar cada imagen con el commit.** Si la imagen se llama `docuchat:3f2a9c1`, sabes exactamente qué código corre en producción y puedes volver a cualquier versión anterior en segundos. `latest` sola no te dice nada.

**SSM en vez de SSH.** Para que GitHub ejecute comandos en tu servidor no hace falta abrir el puerto SSH a Internet. AWS Systems Manager (SSM) manda el comando a través del propio AWS y el servidor solo necesita un permiso en su rol. Es más seguro y es lo que se usa en empresas.

**Secretos.** Las claves de AWS van en *GitHub Secrets*: cifradas, no se ven en los logs y nunca en el código.

---

### Antes de empezar

```bash
git checkout main && git pull
git checkout -b semana18-cicd
```

---

### Martes 23 · 1 h · Build y push automáticos

**Paso 1 · Secretos en GitHub (10 min).** Repo → Settings → Secrets and variables → Actions → *New repository secret*:

| Nombre | Valor |
|---|---|
| `AWS_ACCESS_KEY_ID` | La clave del usuario `marco-cli` |
| `AWS_SECRET_ACCESS_KEY` | Su secreto |
| `AWS_REGION` | `eu-south-2` (o la tuya) |
| `ECR_REGISTRY` | `123456789012.dkr.ecr.eu-south-2.amazonaws.com` |
| `EC2_INSTANCE_ID` | El id de tu instancia (`i-0abc...`), en la consola de EC2 |
| `APP_URL` | `https://docuchat-marco.duckdns.org` |

> Lo ideal es que GitHub se autentique en AWS con OIDC, sin claves de larga duración. Para un proyecto personal valen las claves en Secrets; menciónalo en el README como mejora pendiente.

**Paso 2 · El workflow (40 min).** Crea `.github/workflows/docuchat-deploy.yml` en la raíz del repo:

```yaml
name: DocuChat deploy

on:
  push:
    branches: [main]
    paths: ["projects/02-docuchat/**", ".github/workflows/docuchat-deploy.yml"]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: projects/02-docuchat
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
      - run: uv sync
      - run: uv run ruff check .
      - run: uv run pytest -v
        env:
          GOOGLE_API_KEY: clave-de-ci

  build-and-push:
    needs: test            # solo si los tests pasan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
      - uses: aws-actions/amazon-ecr-login@v2
      - name: Build y push
        working-directory: projects/02-docuchat
        run: |
          IMAGEN=${{ secrets.ECR_REGISTRY }}/docuchat
          docker build -t $IMAGEN:${{ github.sha }} -t $IMAGEN:latest .
          docker push $IMAGEN:${{ github.sha }}
          docker push $IMAGEN:latest
```

**Paso 3 · Probarlo (10 min).** Haz un cambio pequeño en DocuChat (por ejemplo, el texto de `/health` o la descripción de la app), commit, push de la rama, PR y merge.

**Está bien si** en **Actions** ves los dos jobs en verde y en ECR aparece una imagen con la etiqueta del commit.

---

### Miércoles 24 · 1 h · Algoritmos

Usa `TreeNode` y `desde_lista` de la semana 16.

**Lowest Common Ancestor of a BST** (Medium) → `practice/algoritmos/lca_bst.py`

~~~python
def lowest_common_ancestor(root, p: int, q: int) -> int:
    """Devuelve el valor del ancestro común más bajo de p y q en un árbol binario de búsqueda."""
    ...


if __name__ == "__main__":
    arbol = desde_lista([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5])
    assert lowest_common_ancestor(arbol, 2, 8) == 6
    assert lowest_common_ancestor(arbol, 2, 4) == 2
    print("OK")
~~~

<details>
<summary>Pista</summary>
En un BST, lo menor está a la izquierda. Si p y q son menores que el nodo, el ancestro está a la izquierda; si son mayores, a la derecha; si no, es este nodo.
</details>

**Binary Tree Level Order Traversal** (Medium) → `practice/algoritmos/level_order.py`

~~~python
def level_order(root) -> list[list[int]]:
    ...


if __name__ == "__main__":
    assert level_order(desde_lista([3, 9, 20, None, None, 15, 7])) == [[3], [9, 20], [15, 7]]
    assert level_order(None) == []
    print("OK")
~~~

<details>
<summary>Pista</summary>
BFS con una cola (`collections.deque`). Procesa el nivel entero de una vez: mira cuántos nodos hay en la cola antes de empezar el nivel.
</details>

---

### Jueves 25 · 1 h · Desplegar en la EC2

**Paso 1 · Permisos (10 min).**

- IAM → Roles → `docuchat-ec2` → Add permissions → `AmazonSSMManagedInstanceCore`. Con esto el servidor acepta comandos por SSM.
- IAM → Users → `marco-cli` → Add permissions → `AmazonSSMFullAccess`. Con esto tus credenciales pueden enviar esos comandos.
- Reinicia la instancia (EC2 → Reboot). Si la IP cambia, actualiza DuckDNS.

Comprueba en *Systems Manager → Fleet Manager* que aparece tu instancia (puede tardar unos minutos).

**Paso 2 · Añadir el despliegue al workflow (35 min).** Al final de `docuchat-deploy.yml`:

```yaml
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}
      - name: Actualizar el servidor
        run: |
          COMANDO="cd /home/ec2-user/docuchat && \
            aws ecr get-login-password --region ${{ secrets.AWS_REGION }} | docker login --username AWS --password-stdin ${{ secrets.ECR_REGISTRY }} && \
            IMAGE_TAG=${{ github.sha }} docker compose pull api && \
            IMAGE_TAG=${{ github.sha }} docker compose up -d api"
          ID=$(aws ssm send-command \
            --instance-ids ${{ secrets.EC2_INSTANCE_ID }} \
            --document-name AWS-RunShellScript \
            --parameters "commands=[\"$COMANDO\"]" \
            --query Command.CommandId --output text)
          aws ssm wait command-executed --command-id $ID --instance-id ${{ secrets.EC2_INSTANCE_ID }}
      - name: Comprobar que responde
        run: |
          sleep 15
          curl --fail --retry 5 --retry-delay 5 ${{ secrets.APP_URL }}/health
```

**Paso 3 · Probarlo de punta a punta (15 min).** Cambia otra vez algo visible (por ejemplo, añade `"version": "1.1"` a la respuesta de `/health`), PR y merge.

**Está bien si** los tres jobs salen en verde y `https://…/health` muestra el cambio **sin que hayas entrado al servidor**.

---

### Sábado 27 · 1,5 h

**Técnico, 30 min · Rollback.** Practícalo ahora, con calma, y no por primera vez el día que algo se rompa.

1. En ECR, copia la etiqueta (sha) de la imagen **anterior**.
2. Entra al servidor por SSH y ejecuta:

    ```bash
    cd ~/docuchat
    IMAGE_TAG=<sha-anterior> docker compose up -d api
    docker compose ps   # la columna IMAGE debe mostrar la etiqueta anterior
    ```

3. Comprueba en `https://…/health` que ha vuelto la versión anterior (sin el `"version": "1.1"`).
4. Vuelve a la última con `IMAGE_TAG=<sha-último> docker compose up -d api`.
5. Escribe el procedimiento en el README de DocuChat, sección **Deployment → Rollback**, en 4 líneas.

**Carrera, 1 h:** 1 candidatura (40 min) y 1 mensaje de networking (20 min).

**Opcional (si te sobra 1 h esta semana):** un examen de práctica de AWS Cloud Practitioner en [AWS Skill Builder](https://skillbuilder.aws) para ver tu nivel. Si no, lo haces en la semana 20.

---

### Domingo 28 · 15 min · Cierre y checkpoint de febrero

1. **Checkpoint:** compara con la tabla del roadmap (fin de S18: DocuChat en AWS con CI/CD; 28 problemas, 11 candidaturas y 6 contactos).
2. Log semanal.
3. PR de la rama y merge, como siempre.

---

✅ **Checklist**
- [ ] Merge a `main` → tests → imagen en ECR con la etiqueta del commit
- [ ] El servidor se actualiza solo por SSM y el workflow comprueba `/health`
- [ ] Rollback probado y documentado
- [ ] Ningún secreto en el código ni en los logs
- [ ] 2 problemas de árboles
- [ ] 1 candidatura y 1 mensaje

---

### 🆘 Si te atascas

| Problema | Solución |
|---|---|
| `InvalidInstanceId` en SSM | La instancia no está registrada en SSM: revisa el permiso `AmazonSSMManagedInstanceCore` del rol y reinicia. |
| El comando de SSM falla | Systems Manager → Run Command → historial: ahí ves el error exacto del servidor. |
| `docker: command not found` en SSM | SSM ejecuta como root: comprueba que `docker compose version` funciona con `sudo` en el servidor. |
| El job `deploy` pasa pero la app no cambia | Comprueba que `compose.yml` usa `${IMAGE_TAG:-latest}` en la imagen. |
| `curl --fail` falla | La app tarda en arrancar: sube el `sleep` a 30 o revisa `docker compose logs api` en el servidor. |
