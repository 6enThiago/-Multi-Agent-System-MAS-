# Principios Fundamentales del MAS

> *"Un sistema simple que funciona bien vale más que uno grande que falla."*

Doctrina de construcción del proyecto. Todo código, skill o decisión de arquitectura debe respetar estos 7 principios. Si algo los viola, se rechaza o se justifica explícitamente.

---

## 1. Un agente, una responsabilidad

Cada agente hace **una sola cosa bien** (programar, analizar, documentar). Un agente que "hace de todo" se vuelve impredecible.

- **Regla operativa:** si la descripción de un agente contiene "y además…", hay que partirlo en dos.
- **En el código:** `mas/agent.py` → clase `Agente` con un `prompt_sistema` y un rol único. No conoce otros agentes, ni orquestación, ni formato de salida (ese es el contrato).

## 2. Un orquestador al centro

El orquestador recibe la petición, decide qué agente la resuelve y junta los resultados. Los agentes **no se hablan entre sí** de forma caótica.

- **Regla operativa:** toda comunicación entre agentes pasa por el orquestador.
- **En el código:** `mas/orchestrator.py` → la cadena la controla él; ningún agente llama a otro.

## 3. Contexto mínimo

Cada agente recibe **solo lo que necesita**, no toda la conversación.

- **Regla operativa:** el agente N recibe la tarea + la salida del agente N-1. Nada más.
- **En el código:** `mas/orchestrator.py` → variable `contexto` que solo guarda la salida del paso anterior.

## 4. Salidas estandarizadas

Todos los agentes devuelven el resultado con el **mismo formato**: `estado`, `resultado`, `errores`.

- **Regla operativa:** ningún componente devuelve texto suelto; siempre el contrato.
- **En el código:** `mas/result.py` → `ResultadoAgente` (contrato inmutable). El orquestador devuelve `Informe` con el mismo formato más la traza de pasos.

## 5. Humano en el control

Las acciones importantes (borrar, enviar, modificar archivos críticos) **piden confirmación** antes de ejecutarse.

- **Regla operativa:** ninguna acción destructiva o irreversible se ejecuta sin confirmación explícita. Sin quién decida → se niega (seguro por defecto).
- **En el código:** `mas/entorno.py` → toda herramienta destructiva previsualiza con `confirmar=False` y solo corre con `confirmar=True` tras autorización. Los permisos por agente viven en `teams/*.yaml`.
- **Estados resultantes:** `ok` (autorizado), `rechazado` (el humano dijo no), `denegado` (sin permiso en el YAML), `error` (ruta bloqueada, herramienta desconocida…).

## 6. Todo verificable

Si no se puede probar, no se puede confiar. Las skills de test (`test-skills`) y QA (`orquestador-qa`) son clave.

- **Regla operativa:** cada módulo nuevo llega con sus tests; el pipeline completo corre sin red ni claves gracias al proveedor falso.
- **En el código:** `tests/` (unittest, sin dependencias) + `mas/providers/fake.py` (proveedor determinista).

## 7. Empezar pequeño y modular

Construir por incrementos mínimos que funcionan de punta a punta. Primero profundo, luego ancho.

- **Regla operativa:** cada hito deja el sistema **funcionando y testeado**; no se empieza un frente nuevo dejando otro a medias.
- **Hito actual (v0.3.0):** sistema unificado — un solo `Entorno` con permisos por YAML, previsualización, autorización por consola y auditoría JSONL; equipos en `equipos/` (esquema con `orquestador` validado). **Siguiente:** proveedores reales (Anthropic, la clave ya está en `.env`), bucle agente↔herramientas con LLM real y modo paralelo.

## 8. Convención de nuevas herramientas (regla de oro)

Todo lo que se agregue como herramienta sigue este orden fijo:

1. Escribir la función **con el decorador** `@herramienta(...)`, cuya firma declara `confirmar=False` (el decorador lo exige: sin eso, no se registra).
2. Añadir el nombre en el **YAML del agente** que la necesite (`teams/*.yaml`). Sin nombre ahí → `denegado`.
3. Sus procesos que modifican el entorno corren con `confirmar=True`, solo después de la autorización.
4. Añadir sus tests en `tests/` (principio: todo verificable).

---

## Mapa principio → código

| Principio | Archivo |
|---|---|
| Una responsabilidad | `mas/agent.py`, `Equipo` (`mas/entorno.py`) |
| Orquestador al centro | `mas/orchestrator.py`, campo `orquestador` en `equipos/*.yaml` |
| Contexto mínimo | `mas/orchestrator.py` (`contexto`) |
| Salidas estandarizadas | `mas/result.py` (contrato inmutable: ok/rechazado/denegado/error) |
| Humano en el control | `mas/entorno.py` (permisos → preview → autorización) + `equipos/*.yaml` |
| Todo verificable | `tests/` (43 tests), `mas/providers/fake.py`, auditoría `logs/herramientas.jsonl` |
| Empezar pequeño | `docs/PRINCIPIOS.md` (este documento), `AVANCES.md` |
| Regla de oro de herramientas | `mas/tools.py` (decorador), `mas/herramientas.py` (herramientas built-in) |

> **Situación actual (2026-10-18):** convergencia completada — una sola línea (`mas/` + `equipos/`)
> que unifica lo mejor de `mas/` (contrato inmutable, preview antes de preguntar, 43 tests,
> orquestador en cadena) y de `core/` (auditoría JSONL, validación de equipos, confirmación por
> consola). `core/` y `teams/` fueron eliminados tras verificar la matriz completa en vivo.
