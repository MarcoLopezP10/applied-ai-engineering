# Semana 8 · 14–20 dic · Exámenes del term 1 (modo mínimo, 2 h)

[← Semana 7](semana-07.md) · [Roadmap](../applied-ai-engineering-roadmap.md) · [Semana 9 →](semana-09.md)

🎯 **Objetivo:** no parar del todo durante los exámenes y dejar resuelto lo que necesitas saber del máster antes de Navidad.

**Por qué esta semana existe:** cortar del todo dos semanas hace que cueste el doble volver. Con 2 horas mantienes el hábito y resuelves dos cosas que solo se pueden hacer antes de vacaciones (en Navidad IE no contesta correos).

| Día | Tiempo | Bloque | Qué haces |
|---|:---:|---|---|
| Miércoles 16 | 1 h | Algoritmos | Repasar 2 fallados + Product of Array Except Self |
| Sábado 19 | 1 h | Carrera | Correo a IE + fechas reales de 15 empresas |
| Domingo 20 | 15 min | Cierre | Log y preparar la Navidad |

No hay bloque técnico ni rama esta semana.

---

### Miércoles 16 · 1 h · Algoritmos

1. **Repaso (25 min).** Abre `practice/algoritmos/README.md` y elige los 2 problemas en los que pusiste "¿Solo? = no". Resuélvelos otra vez **en un archivo nuevo, sin mirar el anterior**. Si ahora salen, cambia la fila a "sí (2.º intento)".
2. **Product of Array Except Self** (Medium, 30 min) → `practice/algoritmos/product_except_self.py`:

~~~python
"""
Product of Array Except Self · NeetCode 150 · Arrays & Hashing
Patrón:
Complejidad: O(?) tiempo, O(?) espacio
Restricción del enunciado: sin usar la división.
"""


def product_except_self(nums: list[int]) -> list[int]:
    ...


if __name__ == "__main__":
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6]
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0]
    print("OK")
~~~

<details>
<summary>Pista</summary>
El resultado en la posición i es (producto de todo lo que hay a su izquierda) × (producto de todo lo que hay a su derecha). Calcula una pasada de izquierda a derecha y otra de derecha a izquierda.
</details>

```bash
git checkout main && git pull
git add practice/algoritmos && git commit -m "Algoritmos: repaso y Product of Array Except Self" && git push
```

En semanas sin rama puedes hacer commit directo a `main`: es solo práctica de algoritmos.

---

### Sábado 19 · 1 h · Carrera

**1. Correo a IE (20 min).** Envíalo al coordinador académico del máster, con copia a IE Careers:

> **Asunto:** Consulta sobre capstone, certificaciones AWS y prácticas en el term 3
>
> Hola [nombre]:
>
> Soy Marco López Prieto, del MBDS. Tengo tres preguntas para planificar el term 3:
>
> 1. ¿Cómo se asignan las empresas de los *corporate projects* del capstone? ¿Se puede pedir un proyecto de IA o de ingeniería de datos?
> 2. ¿El programa cubre los vouchers de los exámenes AWS Certified Cloud Practitioner y AWS Certified Data Engineer? Si es así, ¿en qué fechas se suelen hacer?
> 3. Mi idea es cursar la concentración Advanced AI. Si una empresa me ofreciera unas prácticas durante el periodo electivo, ¿serían compatibles con la concentración?
>
> Muchas gracias.
> Un saludo,
> Marco

**2. Fechas reales de 15 empresas (40 min).**

1. Elige 15 empresas de la tabla de olas de tu doc privado: unas 5 de la ola 1 (graduate y Big Tech), 5 de la ola 2 y 5 de la ola 3.
2. Para cada una, entra en su página de empleo y busca "graduate", "junior", "AI engineer" o "forward deployed".
3. En el Excel, apunta en la hoja de empresas:
    - si hay oferta abierta ahora o no
    - la fecha de apertura o de cierre si aparece
    - el enlace
4. Crea una alerta de LinkedIn Jobs para cada uno de estos títulos, en Madrid: "AI Engineer", "Forward Deployed Engineer", "Machine Learning Engineer" y "Graduate Software Engineer".

**Por qué ahora:** en enero abren muchos programas y quieres enterarte el día que salen, no tres semanas después.

---

### Domingo 20 · 15 min · Cierre y preparar Navidad

1. Rellena tu entrada en `resources/log-semanal.md` y haz commit a `main`.
2. Comprueba que tienes **Docker Desktop** instalado y abierto (lo necesitas el lunes 21). En un Mac Intel, descarga la versión para "Mac with Intel chip" desde docker.com.
3. Lee la [semana 9](semana-09.md). La Navidad son 3 semanas a 10–12 h: es la parte más intensa del plan.

---

✅ **Checklist**
- [ ] 2 problemas fallados repetidos + 1 nuevo
- [ ] Correo a IE enviado
- [ ] 15 empresas con su estado y enlace en el Excel
- [ ] 4 alertas de LinkedIn creadas
- [ ] Docker Desktop instalado
