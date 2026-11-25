# Log semanal

Cada domingo, 15 minutos. La entrada más reciente va arriba. Plan completo en [`applied-ai-engineering-roadmap.md`](applied-ai-engineering-roadmap.md).

---

## Semana 5 · 23–29 nov 2026
- Horas: más de las previstas (3,5 h técnico · 1 h algoritmos · 1 h carrera); no las medí
- Hecho:
    - Test de tareas por puesto: AI Engineer 5/5 · FDE 5/6 · ML Engineer 4/6 · Software Engineer 3/5
    - Nuevo plan semana a semana (Applied AI Engineering Roadmap)
    - Code Analyzer: salida validada con Pydantic + reintento con el error, y fallback de modelos cuando Gemini da 503/429
    - Comparación de temperaturas 0.2 vs 0.8 en 3 archivos: los bugs reales salen con las dos; las invenciones aparecen en lo que añade alrededor
    - Prompt library con 5 técnicas: few-shot fija el formato; JSON es la que más cambia el resultado
    - Carrera: feedback pedido a Deloitte/Amazon, Revolut revisado y 2 ofertas de la ola 1 apuntadas como "Por enviar"
- Algoritmos (acumulado): 2 (Contains Duplicate, Valid Anagram)
- Candidaturas (acumulado): 0 · Contactos (acumulado): 0
- Qué falló y qué cambio la semana que viene:
    - Gemini (`gemini-3.8-flash`) estuvo caído casi toda la semana (503/429). Cada ejecución la respondió un modelo de respaldo distinto y eso ensució la comparación de temperaturas. Para comparar, fijar un solo modelo.
    - La semana se me fue de horas junto con el máster. Medir las horas de verdad para ver si el plan es realista.
