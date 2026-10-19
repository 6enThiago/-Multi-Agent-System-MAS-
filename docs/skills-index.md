# Índice de Skills del Proyecto MAS

Inventario completo de habilidades (skills) disponibles en el sistema multi-agente, organizadas por categoría según su función dentro del flujo del proyecto.

---

## 📦 Skills integradas del sistema (built-in)

Son provistas por el propio OpenCode y **no se pueden mover** a las carpetas del proyecto. Se cargan automáticamente con el comando `skill`.

| ID | Propósito | Cuándo usarla |
|---|---|---|
| `opencode` | Guía de referencia de OpenCode: configuración (`opencode.json`), CLI, MCP, plugins, API, SDK, cliente, migración V1→V2 y troubleshooting. | Cualquier duda sobre cómo funciona o se configura OpenCode mismo. |
| `report` | Convierte un problema/bug de OpenCode en un issue de GitHub con diagnóstico estándar y pasos de reproducción; lo publica con `gh`. | Cuando el usuario quiera reportar un fallo de OpenCode. |

---

## 🗂 Skills del proyecto (`.opencode/skills/`)

Organizadas por categoría, alineadas con las capas del MAS (Orquestador → Agentes → QA → Registro).

### 🤖 orquestacion/

| ID | Archivo | Propósito |
|---|---|---|
| `auto-agentes` | `orquestacion/auto-agentes/SKILL.md` | Ejecuta y encadena los agentes del MAS: asigna la tarea, define el orden/dependencias, pasa salidas entre agentes, reintenta fallos una vez y entrega un resumen final. |

### ✅ calidad/

| ID | Archivo | Propósito |
|---|---|---|
| `orquestador-qa` | `calidad/orquestador-qa/SKILL.md` | Pipeline de control de calidad completo. Ejecuta en orden: `integridad-archivos` → `auto-agentes` → `test-skills` → `doc-avances`, verificando cada paso antes de continuar. |
| `test-skills` | `calidad/test-skills/SKILL.md` | Prueba skills con casos normal, límite y de entrada inválida; reporta resultados en tabla y sugiere correcciones sin modificar nada. |

### 🔧 mantenimiento/

| ID | Archivo | Propósito |
|---|---|---|
| `integridad-archivos` | `mantenimiento/integridad-archivos/SKILL.md` | Edición segura de archivos: detecta dependencias (imports, configs, referencias), aplica cambios mínimos y verifica que nada quedó roto. |

### 📝 documentacion/

| ID | Archivo | Propósito |
|---|---|---|
| `doc-avances` | `documentacion/doc-avances/SKILL.md` | Registra el progreso en `AVANCES.md` en formato fecha/hecho/estado/siguiente paso, orden cronológico inverso. Solo toca documentación. |

---

## 🔄 Flujo de referencia (pipeline QA)

```
integridad-archivos ──▶ auto-agentes ──▶ test-skills ──▶ doc-avances
   (archivos sanos)     (corren agentes)  (validan skills)  (registra resultado)
```

Si cualquier paso falla, el pipeline se detiene y reporta antes de continuar.

---

## 🧭 Criterio de organización

| Categoría | Agrupa skills que... |
|---|---|
| `orquestacion/` | Ejecutan o coordinan agentes del MAS. |
| `calidad/` | Verifican que el sistema (archivos, agentes, skills) funcione bien. |
| `mantenimiento/` | Modifican o reparan archivos del proyecto de forma segura. |
| `documentacion/` | Registran progreso y conocimiento del proyecto. |

---

## ➕ Cómo añadir una skill nueva

1. Crear `.opencode/skills/<categoria>/<id-de-la-skill>/SKILL.md` (el **ID es el nombre del último directorio**, en kebab-case).
2. Añadir frontmatter con `name` y una `description` clara de cuándo usarla (sin `description` no se anuncia al modelo).
3. Las carpetas `scripts/` y `references/` junto a `SKILL.md` sirven para archivos de apoyo (rutas relativas al directorio de la skill).

> **Nota:** los archivos `.txt` en la raíz no los detecta OpenCode; las skills deben ser `.md` dentro de `.opencode/skills/`.
