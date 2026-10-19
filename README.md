# Multi-Agent System (MAS)

Una herramienta de línea de comandos (CLI) y aplicación web que permite configurar equipos de agentes de IA especializados —por ejemplo, un investigador, un redactor y un corrector— para que colaboren autónomamente en la investigación y redacción de informes, o en la gestión de proyectos y tareas.

---

## 📋 Índice

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Agentes incluidos](#-agentes-incluidos)
- [Requisitos previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Roadmap](#-roadmap)
- [Licencia](#-licencia)

---

## 📖 Descripción

**Multi-Agent System (MAS)** es un orquestador de agentes de IA que coordina un equipo de agentes especializados, cada uno con un rol definido, para ejecutar flujos de trabajo de forma autónoma y colaborativa.

En lugar de interactuar con un único modelo de lenguaje, defines un **equipo** de agentes con roles complementarios. El sistema se encarga de:

1. Recibir una tarea o objetivo del usuario.
2. Descomponerla en subtareas.
3. Asignar cada subtarea al agente adecuado.
4. Encadenar las salidas de un agente como entrada del siguiente.
5. Devolver un resultado final consolidado (informe, documento, plan de proyecto, etc.).

### Casos de uso

- **Redacción de informes:** un investigador recopila información, un redactor elabora el borrador y un corrector lo revisa y pule.
- **Gestión de proyectos:** un analista descompone el proyecto, un planificador organiza tareas y plazos, y un revisor valida el plan.
- **Investigación:** un agente de búsqueda recoge datos, un sintetizador los resume y un verificador contrasta fuentes.

---

## ✨ Características

- **Equipos configurables:** define los agentes, sus roles, prompts y modelos en un archivo de configuración YAML/JSON.
- **Flujos de trabajo autónomos:** los agentes colaboran en cadena (pipeline) sin intervención manual entre pasos.
- **Múltiples orígenes de modelos:** compatible con OpenAI, Anthropic Claude, modelos locales (Ollama) y otros proveedores.
- **Modo CLI:** ejecuta equipos desde la terminal con un único comando.
- **Modo Web:** interfaz visual para configurar equipos, lanzar tareas y seguir el progreso en tiempo real.
- **Plantillas predefinidas:** equipos listos para usar (investigación + redacción, gestión de tareas, etc.).
- **Historial y trazabilidad:** registro de cada paso, salidas intermedias y coste estimado de cada ejecución.
- **Extensible:** añade nuevos agentes y roles sin modificar el núcleo del sistema.

---

## 🏗 Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                     Interfaz (CLI / Web)                │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     Orquestador (Orchestrator)          │
│  · Recibe la tarea                                      │
│  · Lee la configuración del equipo                      │
│  · Secuencia y coordina a los agentes                   │
│  · Gestiona el estado y los errores                     │
└───────┬─────────────────┬─────────────────┬─────────────┘
        │                 │                 │
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Investigador │  │   Redactor   │  │  Corrector   │
│  (Researcher) │─▶│   (Writer)   │─▶│  (Reviewer)  │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Resultado final      │
              │  (informe / plan /…)  │
              └───────────────────────┘
```

**Componentes principales:**

| Componente | Responsabilidad |
|---|---|
| **Orquestador** | Recibe la tarea, aplica la configuración del equipo y coordina la ejecución en cadena de los agentes. |
| **Agente** | Unidad autónoma con un rol, un prompt de sistema, un modelo asociado y una herramienta opcional (búsqueda, lectura de archivos, etc.). |
| **Memoria / Contexto** | Mantiene el historial compartido entre agentes durante la ejecución. |
| **Interfaz CLI** | Punto de entrada de terminal (`mas run`, `mas team list`, etc.). |
| **Interfaz Web** | Panel visual para configurar equipos, lanzar tareas y ver el progreso. |
| **Almacenamiento** | Guarda configuraciones de equipos, historial de ejecuciones y resultados. |

---

## 🤖 Agentes incluidos

| Rol | Nombre | Función |
|---|---|---|
| 🔍 **Investigador** | `researcher` | Busca, recopila y verifica información relevante para la tarea. |
| ✍️ **Redactor** | `writer` | Convierte la investigación en un documento estructurado y coherente. |
| ✅ **Corrector** | `reviewer` | Revisa, corrige estilo y gramática, y valida que el resultado cumpla los objetivos. |
| 📊 **Analista** | `analyst` | Descompone proyectos en tareas y dependencias *(modo gestión de proyectos)*. |
| 📅 **Planificador** | `planner` | Organiza tareas en un plan con plazos y prioridades *(modo gestión de proyectos)*. |

> Todos los agentes son personalizables: puedes cambiar sus prompts, asignarles otro modelo o crear agentes nuevos.

---

## ⚙️ Requisitos previos

- **Python** ≥ 3.10
- **pip** (gestor de paquetes)
- Una **clave de API** de al menos un proveedor de modelos (OpenAI, Anthropic, etc.) o un servidor local como **Ollama**
- *(Opcional)* **Node.js** ≥ 18 para el servidor web

---

## 📦 Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/Multi-agent-System-MAS.git
cd Multi-agent-System-MAS

# 2. Crear un entorno virtual
python -m venv .venv

# Activarlo
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
copy .env.example .env     # Windows
cp .env.example .env       # macOS / Linux
# Editar .env con tus claves de API
```

---

## 🔧 Configuración

### Variables de entorno (`.env`)

```env
# Proveedor por defecto
MAS_PROVIDER=openai

# Claves de API (solo se necesita la del proveedor que uses)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Modelo por defecto
MAS_MODEL=gpt-4o

# Modo de ejecución: sequential (cadena) | parallel (paralelo)
MAS_MODE=sequential
```

### Definición de un equipo (`teams/informe.yaml`)

```yaml
name: Equipo de Informes
description: Investiga, redacta y revisa informes automáticamente

agents:
  - id: researcher
    role: Investigador
    model: gpt-4o
    system_prompt: >
      Eres un investigador riguroso. Recopila datos fiables,
      cita tus fuentes y entrega un resumen estructurado con
      hallazgos clave.

  - id: writer
    role: Redactor
    model: gpt-4o
    system_prompt: >
      Eres un redactor profesional. Convierte la investigación
      recibida en un informe claro, bien estructurado y con
      introducción, desarrollo y conclusión.

  - id: reviewer
    role: Corrector
    model: gpt-4o
    system_prompt: >
      Eres un corrector experto. Revisa ortografía, estilo,
      coherencia y rigor. Devuelve el texto corregido y una
      lista de mejoras aplicadas.

workflow:
  type: sequential          # sequential | parallel
  steps:
    - agent: researcher
    - agent: writer
      depends_on: [researcher]
    - agent: reviewer
      depends_on: [writer]

output:
  format: markdown
  path: ./outputs/
```

---

## 🚀 Uso

### Modo CLI

```bash
# Listar equipos configurados
mas team list

# Ejecutar un equipo con una tarea
mas run --team informe --task "Informe sobre el impacto de la IA en la educación"

# Ejecutar con un equipo predefinido
mas run --template research-writing --task "Análisis del mercado de software en 2026"

# Ejecutar un solo agente
mas agent run researcher --task "Busca las últimas tendencias de LLMs"

# Ver el historial de ejecuciones
mas history
```

### Modo Web

```bash
# Iniciar el servidor web
mas serve --port 8000
# o
python -m mas.web
```

Luego abre **http://localhost:8000** en tu navegador:

1. **Equipos:** crea o edita equipos de agentes desde una interfaz visual.
2. **Ejecutar:** introduce la tarea, selecciona el equipo y lanza la ejecución.
3. **Progreso:** sigue en tiempo real cada paso, la salida de cada agente y el resultado final.
4. **Historial:** consulta ejecuciones anteriores y descarga los resultados.

---

## 📁 Estructura del proyecto

```
Multi-agent-System-MAS/
├── README.md
├── requirements.txt
├── .env.example
├── pyproject.toml
├── mas/                        # Paquete principal
│   ├── __init__.py
│   ├── cli.py                  # Punto de entrada CLI (Click/Typer)
│   ├── orchestrator.py         # Orquestador de agentes
│   ├── agent.py                # Definición y ejecución de agentes
│   ├── providers/              # Adaptadores de modelos
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   └── ollama.py
│   ├── teams/                  # Carga de configuración de equipos
│   │   └── loader.py
│   ├── storage/                # Historial y resultados
│   └── web/                    # Aplicación web (FastAPI + frontend)
│       ├── app.py
│       └── static/
├── equipos/                    # Configuraciones de equipos (YAML)
│   ├── laboral.yaml
│   └── demo.yaml
├── outputs/                    # Resultados generados
├── tests/                      # Pruebas
└── docs/                       # Documentación adicional
```

---

## 🗺 Roadmap

- [x] Definición de arquitectura y diseño del sistema
- [ ] Núcleo del orquestador con flujo secuencial
- [ ] Proveedores de modelos (OpenAI, Anthropic, Ollama)
- [ ] CLI básica (`mas run`, `mas team list`)
- [ ] Plantillas de equipos predefinidas
- [ ] Modo paralelo de ejecución de agentes
- [ ] Interfaz web con progreso en tiempo real
- [ ] Herramientas externas para agentes (búsqueda web, lectura de archivos)
- [ ] Modo gestión de proyectos (analista + planificador)
- [ ] Exportación de resultados a PDF / DOCX
- [ ] Sistema de plugins para agentes personalizados

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Para empezar:

1. Haz un *fork* del repositorio.
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Realiza tus cambios y añade pruebas.
4. Envía un *pull request* describiendo los cambios.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
