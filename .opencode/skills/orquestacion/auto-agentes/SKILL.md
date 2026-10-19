---
name: auto-agentes
description: Automatiza la ejecución de los agentes del sistema multi-agente. Úsala siempre que se pida correr, lanzar, encadenar o programar agentes, o cuando una tarea deba repartirse entre varios de ellos.
---

# Auto-Agentes

1. Identifica la tarea y elige el agente (o agentes) que le corresponde.
2. Si hay varios, define el orden: qué corre primero y qué depende de qué.
3. Ejecuta cada agente pasándole solo el contexto que necesita.
4. Pasa la salida de un agente como entrada del siguiente.
5. Si uno falla: reintenta una vez; si vuelve a fallar, detén la cadena y reporta el error.
6. Al terminar, entrega un resumen: agentes ejecutados, resultado de cada uno y errores.

Reglas:
- No ejecutes agentes que no se pidieron o no hacen falta.
- No sigas la cadena si un paso crítico falló.
