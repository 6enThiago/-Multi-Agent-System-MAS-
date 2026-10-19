---
name: orquestador-qa
description: Ejecuta y supervisa las demás skills (auto-agentes, integridad-archivos, doc-avances, test-skills) y confirma que todo funcione bien. Úsala cuando se pida un chequeo general, revisar que todo funcione o correr el flujo completo.
---

# Orquestador QA

Ejecuta en este orden:
1. `integridad-archivos`: verifica que los archivos estén sanos.
2. `auto-agentes`: corre los agentes.
3. `test-skills`: prueba que las skills respondan bien.
4. `doc-avances`: registra el resultado.

Después de cada paso, confirma que terminó sin errores antes de pasar al siguiente.

Entrega un reporte final:
- ✅ / ❌ por cada skill
- Errores encontrados
- Qué falta corregir

Reglas:
- Si una skill falla, detente y reporta antes de continuar.
- No arregles nada por tu cuenta; solo ejecuta, verifica y reporta.
