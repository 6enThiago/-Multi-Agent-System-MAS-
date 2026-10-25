# MAS — Asistente de archivos en segundo plano

> **Estado del proyecto:** en desarrollo temprano. El núcleo (orquestador, permisos, confirmación humana y auditoría) ya existe y tiene pruebas. La interfaz de chat, el modo segundo plano, el proveedor de IA real y el ejecutable `.exe` **todavía no están implementados**. Consulta [`MEJORAS.md`](MEJORAS.md) para ver el plan detallado.

---

## Índice

1. [Qué es MAS](#qué-es-mas)
2. [Para quién es](#para-quién-es)
3. [Qué hace](#qué-hace)
4. [Principios de diseño](#principios-de-diseño)
5. [Cómo funciona](#cómo-funciona)
6. [Seguridad y control del usuario](#seguridad-y-control-del-usuario)
7. [Distribución como ejecutable](#distribución-como-ejecutable)
8. [Estado actual](#estado-actual)
9. [Instalación para desarrollo](#instalación-para-desarrollo)
10. [Configuración de equipos (YAML)](#configuración-de-equipos-yaml)
11. [Estructura del proyecto](#estructura-del-proyecto)
12. [Pruebas](#pruebas)
13. [Contribuir](#contribuir)
14. [Licencia](#licencia)

---

## Qué es MAS

**MAS (Multi-Agent System)** es una herramienta de escritorio que trabaja **en segundo plano** mientras tú haces otra cosa. Su trabajo es mantener tus archivos ordenados, crear documentos cuando se lo pides y borrar lo que ya no necesitas, siempre **con tu confirmación y mostrándote la ruta exacta** de lo que va a tocar.

Se usa desde una ventana de chat sencilla (un cuadro de texto donde escribes lo que necesitas) y se distribuye como **un único ejecutable** (`.exe` en Windows, binario en macOS/Linux) generado con PyInstaller u otro empaquetador, para que cualquier persona pueda usarlo sin instalar Python.

Por debajo, un equipo de agentes especializados (orquestador, programador, analista, documentador…) se reparte el trabajo. El usuario no necesita saberlo: solo escribe qué quiere.

---

## Para quién es

| Ámbito | Ejemplos de uso |
|---|---|
| **Entorno de trabajo** | Ordenar la carpeta de Descargas por tipo o proyecto, archivar informes antiguos, crear plantillas de actas o notas de reunión, limpiar duplicados y temporales. |
| **Vida cotidiana** | Organizar fotos y documentos personales, crear una lista de compras o un presupuesto en un archivo, borrar instaladores y capturas viejas, mantener el escritorio limpio. |

El público objetivo es **no técnico**: la interfaz debe ser un chat claro, con mensajes de confirmación comprensibles.

---

## Qué hace

### 1. Acomoda archivos
- Clasifica y mueve archivos por tipo, fecha o proyecto dentro de carpetas que **tú autorizas**.
- Siempre muestra primero un **plan previo** (qué se moverá y adónde) y espera tu aprobación.
- Permite **deshacer** el último reordenamiento.

### 2. Crea archivos bajo petición
- Escribes en el chat: *«Crea una nota de reunión para el lunes»* y el sistema genera el archivo.
- Antes de guardar, muestra la ruta de destino y una vista previa.

### 3. Borra archivos rápido y con confirmación
- Escribes: *«Borra los instaladores de Descargas»*.
- MAS lista los archivos candidatos con su **ruta completa** y su tamaño.
- Nada se borra sin tu confirmación explícita.
- Por defecto envía los archivos a la **papelera de reciclaje**, no los elimina de forma permanente.

### 4. Trabaja en segundo plano
- Vive en la **bandeja del sistema** (icono junto al reloj).
- Puede vigilar carpetas y **proponer** acciones (por ejemplo, «hay 14 capturas nuevas, ¿las ordeno?») sin interrumpir lo que haces.
- Las notificaciones piden permiso; **nunca actúa por su cuenta sobre archivos**.

---

## Principios de diseño

Estos principios ya están presentes en el código y guían cada decisión nueva:

1. **Un agente, una responsabilidad.** Cada agente hace una cosa bien y no habla con otros directamente.
2. **Orquestador al centro.** Toda coordinación pasa por el orquestador.
3. **Contexto mínimo.** Cada agente recibe solo lo imprescindible (menos coste y menos errores).
4. **Salidas estandarizadas.** Todo resultado tiene la misma forma: `estado`, `resultado`, `errores`.
5. **Todo verificable.** Un proveedor falso permite probar el sistema completo sin red ni coste.
6. **Humano en el control.** Ninguna acción que modifique el sistema se ejecuta sin previsualización y autorización.
7. **Regla de oro de las herramientas.** Toda herramienta se escribe primero con `confirmar=False` (previsualiza) y solo actúa con `confirmar=True` tras la autorización. El decorador `@herramienta` lo exige mecánicamente.

---

## Cómo funciona

```text
┌──────────────────────────────────────────────────────────┐
│  Interfaz: ventana de chat + icono en bandeja del sistema │
└────────────────────────────┬─────────────────────────────┘
                             │ petición del usuario
                             ▼
┌──────────────────────────────────────────────────────────┐
│  Orquestador: interpreta, reparte, reintenta, reporta     │
└──────┬─────────────────┬──────────────────┬──────────────┘
       ▼                 ▼                  ▼
  Agente(s)         Agente(s)          Agente(s)
       │                 │                  │
       └────── piden herramientas ──────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│  Entorno (única puerta al sistema de archivos)            │
│  permisos → previsualización → CONFIRMACIÓN → ejecución   │
│  → auditoría                                              │
└──────────────────────────────────────────────────────────┘
```

**Flujo de una acción que modifica archivos:**

1. El usuario escribe una petición en el chat.
2. El orquestador la asigna al agente adecuado.
3. El agente propone una herramienta (por ejemplo, `borrar_archivo`).
4. El `Entorno` comprueba que el agente tiene permiso en el YAML del equipo.
5. Se genera una **previsualización** con la ruta exacta.
6. El usuario confirma o rechaza en la interfaz.
7. Solo si confirma, la herramienta se ejecuta de verdad.
8. Queda registrada en el log de auditoría.

Los estados posibles de cualquier acción son: `ok`, `rechazado` (el humano dijo no), `denegado` (el agente no tiene permiso) y `error`.

---

## Seguridad y control del usuario

- **Carpetas autorizadas:** MAS solo opera dentro de las carpetas que el usuario concede explícitamente. Cualquier ruta fuera se bloquea (protección contra `../`, rutas absolutas y enlaces simbólicos).
- **Carpetas protegidas:** las carpetas del sistema (Windows, Archivos de programa, `/etc`, etc.) nunca se pueden tocar, aunque el usuario las autorice por error.
- **Confirmación siempre visible:** la ruta completa y la acción aparecen en el diálogo de confirmación.
- **Papelera por defecto:** el borrado es recuperable.
- **Seguro por defecto:** si no hay interfaz de confirmación disponible, la acción se rechaza.
- **Auditoría:** cada ejecución se registra en `logs/herramientas.jsonl` (fecha, agente, herramienta, estado).
- **Sin envío de archivos a terceros sin aviso:** si se usa un modelo en la nube, el usuario debe saber qué información se envía. Se ofrecerá también modo local (Ollama).
- **Claves de API fuera del ejecutable:** nunca se incrustan en el `.exe`; se guardan en el almacén seguro del sistema.

---

## Distribución como ejecutable

El objetivo es entregar **un solo archivo** que el usuario ejecute con doble clic.

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name MAS --add-data "equipos;equipos" mas/__main__.py
```

> En macOS/Linux el separador de `--add-data` es `:` en lugar de `;`.

Puntos que hay que resolver antes de empaquetar (detalle en [`MEJORAS.md`](MEJORAS.md)):

- Las rutas basadas en `__file__` (`RAIZ`, `ESPACIO`) **no funcionan igual dentro de un ejecutable**. Hay que usar rutas por usuario (`%APPDATA%`, `~/.config`) y `sys._MEIPASS` solo para recursos incluidos.
- Los YAML de equipos y cualquier recurso deben incluirse con `--add-data`.
- La interfaz gráfica debe sustituir a `input()` para las confirmaciones.
- Firmar el ejecutable (Windows) para reducir avisos de antivirus y SmartScreen.

---

## Estado actual

| Capacidad | Estado |
|---|---|
| Orquestador secuencial con reintentos | ✅ Implementado y probado |
| Contrato de salida estandarizado | ✅ Implementado y probado |
| Permisos por agente en YAML | ✅ Implementado y probado |
| Previsualización + confirmación + auditoría | ✅ Implementado y probado (confirmación solo por consola) |
| Bloqueo de rutas fuera del área de trabajo | ✅ Implementado y probado |
| Herramientas `leer_archivo` y `escribir_archivo` | ✅ Implementadas |
| Proveedor falso para pruebas | ✅ Implementado |
| Agentes que **eligen y usan** herramientas por sí mismos | ❌ Pendiente (prioridad máxima) |
| Proveedor de IA real (Anthropic / OpenAI / Ollama) | ❌ Pendiente |
| Herramientas `borrar_archivo`, `mover_archivo`, `crear_carpeta` | ❌ Pendiente |
| Ventana de chat | ❌ Pendiente |
| Ejecución en segundo plano / bandeja del sistema | ❌ Pendiente |
| Vigilancia de carpetas | ❌ Pendiente |
| Empaquetado `.exe` | ❌ Pendiente |

---

## Instalación para desarrollo

**Requisitos:** Python ≥ 3.10.

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/Multi-agent-System-MAS.git
cd Multi-agent-System-MAS

# 2. Crear y activar un entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

Uso actual desde terminal:

```bash
# Cadena de demostración con proveedor falso
python -m mas run --task "Informe de prueba"

# Ejecutar una herramienta como un agente (con confirmación por consola)
python -m mas tool --agent programador --tool escribir_archivo \
    --arg ruta=notas/hola.md --arg contenido="Hola"
```

---

## Configuración de equipos (YAML)

Los equipos viven en `equipos/*.yaml`. Esquema actual:

```yaml
equipo: laboral
descripcion: Equipo para programar, analizar y documentar en el trabajo
orquestador: orquestador

agentes:
  - nombre: orquestador
    rol: Interpreta la petición y reparte la tarea
    herramientas: [leer_archivo]

  - nombre: programador
    rol: Escribe y corrige código
    herramientas: [leer_archivo, escribir_archivo]

  - nombre: analista
    rol: Lee datos y resume resultados (solo lectura)
    herramientas: [leer_archivo]
```

Una herramienta que no aparece en la lista de un agente queda **denegada** para ese agente.

El esquema evolucionará para incluir `prompt_sistema` y `proveedor`/`modelo` por agente (ver `MEJORAS.md`).

---

## Estructura del proyecto

```text
Multi-agent-System-MAS/
├── README.md
├── MEJORAS.md
├── requirements.txt
├── pyproject.toml
├── mas/
│   ├── __init__.py
│   ├── __main__.py          # python -m mas
│   ├── cli.py               # Interfaz de línea de comandos
│   ├── agent.py             # Agente (una responsabilidad)
│   ├── orchestrator.py      # Orquestador en cadena con reintentos
│   ├── result.py            # Contrato de salida estandarizado
│   ├── entorno.py           # Permisos, confirmación y auditoría
│   ├── tools.py             # Registro y decorador @herramienta
│   ├── herramientas.py      # Herramientas de archivos
│   ├── providers/
│   │   ├── __init__.py      # Protocolo Proveedor
│   │   └── fake.py          # Proveedor falso para pruebas
│   └── teams/
│       └── loader.py        # Carga y validación de equipos YAML
├── equipos/
│   ├── laboral.yaml
│   └── demo.yaml
├── tests/
└── logs/                    # Auditoría (se genera en ejecución)
```

---

## Pruebas

```bash
python -m unittest discover -s tests -v
```

---

## Contribuir

1. Haz un *fork* del repositorio.
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`.
3. Toda herramienta nueva debe seguir la **regla de oro** (`confirmar=False` por defecto) y llevar pruebas.
4. Ejecuta las pruebas antes de enviar el *pull request*.

---

## Licencia

Pendiente de definir. Añade un archivo `LICENSE` antes de publicar (por ejemplo MIT) y actualiza esta sección.
