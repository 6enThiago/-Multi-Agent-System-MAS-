# AVANCES

## 2026-10-18 — Convergencia completada: una sola línea (v0.3.0)
- **Fecha:** 2026-10-18
- **Qué se hizo:** Fusión de `mas/` + `core/` en un solo sistema: `mas/entorno.py` unificado (permisos → preview → autorización → ejecución → auditoría JSONL), gestor de equipos con validación completa (`mas/teams/loader.py`), esquema YAML único en `equipos/` (laboral + demo), `main.py` y CLI reescritos sobre el sistema unificado. Eliminados `core/` y `teams/` tras verificar 43/43 tests y la matriz completa en vivo.
- **Estado:** completado
- **Pendiente / siguiente paso:** proveedores reales (Anthropic, clave en `.env`), bucle agente↔herramientas con LLM real y modo paralelo.

## 2026-10-18 — Implementación paralela en `core/`: capa de herramientas con auditoría
- **Fecha:** 2026-10-18
- **Qué se hizo:** Nuevo paquete `core/` con decorador propio `@herramienta(descripción, confirmar=...)`, `CapaHerramientas` (permisos por equipo + confirmación por consola + auditoría JSONL en `logs/herramientas.jsonl`), gestor que valida equipos (`core/gestor.py`), equipo de 4 agentes `equipos/laboral.yaml` (orquestador, programador, analista, documentador), demo `main.py` y `.env` con clave de Anthropic (gitignoreado). Verificado en vivo: los 4 casos de la matriz (ok/denegado/ok/error) y 35/35 tests del núcleo en verde.
- **Estado:** completado
- **Pendiente / siguiente paso:** tests para `core/`; convergencia de las dos implementaciones existentes (`mas/`+`teams/` vs `core/`+`equipos/`, esquemas YAML distintos); proveedores reales con la clave de Anthropic ya disponible.

## 2026-10-18 — Capa de entorno: herramientas, permisos y confirmación (v0.2.0)
- **Fecha:** 2026-10-18
- **Qué se hizo:** Decorador `@herramienta` que exige `confirmar=False` en la firma (regla de oro), herramientas `leer_archivo`/`escribir_archivo` con bloqueo de rutas, permisos por agente en `teams/equipo_demo.yaml`, flujo de autorización en `mas/entorno.py` (estados ok/rechazado/denegado/error) y subcomando `python -m mas tool`. Matriz de autorización verificada en vivo y 35/35 tests en verde.
- **Estado:** completado
- **Pendiente / siguiente paso:** proveedores reales (OpenAI/Anthropic/Ollama), bucle agente↔herramientas con LLM y equipos YAML completos (roles, prompts, modelos).

## 2026-10-18 — Núcleo mínimo v0.1.0 del MAS
- **Fecha:** 2026-10-18
- **Qué se hizo:** Doctrina de 7 principios (`docs/PRINCIPIOS.md`) y núcleo funcional: contrato estandarizado estado/resultado/errores (`mas/result.py`), agente de una sola responsabilidad (`mas/agent.py`), orquestador central en cadena con contexto mínimo y reintentos (`mas/orchestrator.py`), proveedor falso y CLI demo (`python -m mas run --task "..."`). Creadas las 5 skills del proyecto en `.opencode/skills/` y su índice (`docs/skills-index.md`).
- **Estado:** completado (16/16 tests unittest en verde, pipeline verificado de punta a punta)
- **Pendiente / siguiente paso:** proveedores reales (OpenAI/Anthropic/Ollama), carga de equipos desde YAML y capa de herramientas con confirmación humana.
