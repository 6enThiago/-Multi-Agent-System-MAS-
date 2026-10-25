# MEJORAS — Plan técnico del proyecto MAS

Este documento recoge **qué hay que corregir y construir** para pasar del código actual (un núcleo seguro y bien probado) a la herramienta definida en [`README.md`](README.md): un asistente de archivos en segundo plano, con chat, distribuido como ejecutable.

Está basado en el análisis del código real (`agent.py`, `orchestrator.py`, `entorno.py`, `tools.py`, `herramientas.py`, `loader.py`, `cli.py`, `result.py`, proveedores, YAML y tests).

---

## Índice

1. [Diagnóstico en una página](#1-diagnóstico-en-una-página)
2. [Fase 1 — Hacer que los agentes usen herramientas](#2-fase-1--hacer-que-los-agentes-usen-herramientas)
3. [Fase 2 — Un proveedor de IA real](#3-fase-2--un-proveedor-de-ia-real)
4. [Fase 3 — Herramientas del producto](#4-fase-3--herramientas-del-producto)
5. [Fase 4 — Seguridad para un producto de escritorio](#5-fase-4--seguridad-para-un-producto-de-escritorio)
6. [Fase 5 — Interfaz de chat](#6-fase-5--interfaz-de-chat)
7. [Fase 6 — Segundo plano](#7-fase-6--segundo-plano)
8. [Fase 7 — Empaquetado como ejecutable](#8-fase-7--empaquetado-como-ejecutable)
9. [Correcciones técnicas del código actual](#9-correcciones-técnicas-del-código-actual)
10. [Mejoras de tests](#10-mejoras-de-tests)
11. [Decisiones pendientes](#11-decisiones-pendientes)
12. [Orden recomendado](#12-orden-recomendado)

---

## 1. Diagnóstico en una página

**Lo mejor que tiene el proyecto hoy**

- Contrato de salida uniforme e inmutable (`ok / rechazado / denegado / error`).
- Regla de oro `confirmar=False` impuesta por el decorador `@herramienta`.
- `Entorno` como única puerta al disco: permisos → previsualización → autorización → ejecución → auditoría.
- Protección contra path traversal con pruebas.
- `Proveedor` como `Protocol` y proveedor falso determinista.

**Las brechas que separan el código del producto**

| # | Brecha | Impacto |
|---|---|---|
| 1 | Los agentes **no invocan herramientas**. `Proveedor.completar` solo devuelve texto. | Sin esto no hay asistente, solo piezas sueltas. |
| 2 | Solo existe `ProveedorFalso`. `mas run` siempre hace eco. | No hay inteligencia real. |
| 3 | El YAML no define `prompt_sistema` ni modelo. `cli.py` arma el equipo a mano. | Equipos no configurables de verdad. |
| 4 | El campo `orquestador:` del YAML es solo una etiqueta. | Confusión de diseño. |
| 5 | No existen `borrar_archivo`, `mover_archivo`, etc. | Faltan las funciones centrales del producto. |
| 6 | La confirmación usa `input()` de consola. | Imposible en una app con ventana o en segundo plano. |
| 7 | Rutas basadas en `__file__` y carpeta única `espacio_trabajo/`. | Se rompe en el ejecutable y no sirve para trabajar sobre Descargas/Documentos. |

---

## 2. Fase 1 — Hacer que los agentes usen herramientas

**Prioridad máxima.** Es lo que convierte una librería de piezas en un sistema de agentes.

### Qué falta

El bucle: *el modelo propone una herramienta → `Entorno.ejecutar` → el resultado vuelve al modelo → repite hasta dar una respuesta final*.

### Cambios propuestos

1. **Ampliar el contrato del proveedor.** `completar` hoy devuelve `str`. Debe poder devolver texto **o** una petición de herramienta:

   ```python
   @dataclass(frozen=True)
   class LlamadaHerramienta:
       nombre: str
       argumentos: dict

   @dataclass(frozen=True)
   class RespuestaModelo:
       texto: str = ""
       llamada: LlamadaHerramienta | None = None
   ```

2. **Bucle en `Agente`** con límite de iteraciones (por ejemplo, 6) para evitar ciclos infinitos:

   ```text
   para i en 1..MAX_ITER:
       respuesta = proveedor.completar(historial)
       si no hay llamada → devolver texto final
       resultado = entorno.ejecutar(agente, herramienta, args, autorizar)
       añadir resultado al historial
   si se agota → error "demasiadas iteraciones"
   ```

3. **Inyectar el `Entorno` y el autorizador** al construir el agente (no importarlos globalmente).
4. **Describir las herramientas al modelo.** `tools.py` ya guarda `descripcion`; añadir también el esquema de parámetros (derivable de la firma con `inspect`).
5. **Mantener el principio de contexto mínimo:** el historial de herramientas vive solo durante la ejecución de ese agente y no se pasa íntegro al siguiente.
6. **Mantener las cuatro salidas:** un `RECHAZADO` o `DENEGADO` debe volver al modelo como información («el usuario no autorizó») para que pueda explicarlo o proponer otra cosa.

### Criterio de aceptación

Un test con `ProveedorFalso` guionizado que pida `escribir_archivo`, pase por `Entorno`, y termine con una respuesta de texto; sin red.

---

## 3. Fase 2 — Un proveedor de IA real

- Implementar **al menos uno** detrás del `Protocol`: Anthropic u OpenAI (nube) y/o **Ollama** (local, sin enviar datos fuera).
- Para un asistente que ve nombres de archivos personales, ofrecer **modo local** es un argumento de venta fuerte (privacidad).
- Añadir `proveedor` y `modelo` por agente en el YAML, con regla de precedencia clara:

  ```text
  YAML del agente  >  variables de entorno / configuración de usuario  >  valores por defecto
  ```

- Añadir al YAML `prompt_sistema` por agente y hacer que `cli.py` y la futura interfaz construyan los `Agente` **desde el YAML**, eliminando `equipo_demo()`.
- Gestión de errores del proveedor: distinguir fallos transitorios (red, límite de tasa → reintentar con espera) de permanentes (clave inválida → no reintentar).
- Guardar la clave de API en el **almacén seguro del sistema** (librería `keyring`), nunca en el YAML ni dentro del ejecutable.
- Límites de coste: tope de tokens por petición y por sesión.

---

## 4. Fase 3 — Herramientas del producto

Todas deben cumplir la regla de oro (`confirmar=False` previsualiza, `confirmar=True` actúa) y declarar `requiere_confirmacion=True` si modifican algo.

| Herramienta | Qué hace | Confirmación | Notas |
|---|---|---|---|
| `listar_carpeta` | Lista archivos con tamaño y fecha | No | Con límite de resultados. |
| `leer_archivo` | Ya existe | No | Añadir límite de tamaño y rechazo de binarios. |
| `crear_archivo` | Crea un archivo nuevo (no sobrescribe) | Sí | Previsualiza ruta y contenido. |
| `escribir_archivo` | Ya existe (sobrescribe) | Sí | Mostrar si el archivo existe y su tamaño anterior; idealmente un *diff*. |
| `crear_carpeta` | Crea carpetas | Sí | |
| `mover_archivo` | Mueve/renombra | Sí | Previsualiza origen → destino; no sobrescribe sin aviso. |
| `organizar_carpeta` | Propone un **plan** de movimientos por tipo/fecha | Sí (por lote) | Una sola confirmación para el plan completo, mostrando la lista. |
| `borrar_archivo` | Envía a la papelera | Sí | Ver detalle abajo. |
| `buscar_duplicados` | Detecta archivos idénticos (hash) | No | Solo lista; el borrado va por `borrar_archivo`. |

### Detalle de `borrar_archivo`

- Usar `send2trash` para mandar a la **papelera** por defecto; el borrado permanente solo con opción explícita y una confirmación adicional.
- La previsualización debe mostrar: **ruta completa, tamaño, fecha de modificación** y número total de archivos si es un lote.
- **Límite por lote** (por ejemplo, más de 25 archivos exige una segunda confirmación).
- Prohibir borrar carpetas raíz de las zonas autorizadas, el escritorio completo, `Documentos` completa, etc.
- Registrar en la auditoría la ruta completa (hoy se truncan los argumentos a 80 caracteres; para borrados conviene guardar la ruta entera).

### Deshacer

- Guardar un **registro de operaciones reversibles** (movimientos y creaciones) para ofrecer «deshacer lo último».
- Los borrados a la papelera se recuperan desde ahí; indicarlo al usuario.

---

## 5. Fase 4 — Seguridad para un producto de escritorio

El diseño actual limita todo a `espacio_trabajo/`. Para un asistente útil hay que **abrir el alcance de forma controlada**.

1. **Carpetas autorizadas por el usuario.** Sustituir la raíz única por una lista (`Descargas`, `Documentos`, `Escritorio`…) que el usuario concede en un primer arranque y puede cambiar después.
2. **Lista negra de rutas protegidas** (sistema operativo, programas, carpeta de MAS y su configuración), que prevalece sobre cualquier autorización.
3. **Resolver enlaces simbólicos** y comprobar que el destino real sigue dentro de una carpeta autorizada (hoy `resolve()` ayuda, pero falta un test específico).
4. **Autorizador desacoplado de la consola.** `autorizar_por_consola` usa `input()`. Definir una interfaz `Autorizador` con implementaciones: consola, ventana de diálogo, notificación con botones, y «siempre rechazar» para modo desatendido.
5. **Tiempo de espera** en las confirmaciones: si el usuario no responde en N segundos, se rechaza.
6. **Auditoría legible:** mostrar al usuario un historial de «qué hice y cuándo».
7. **Privacidad con modelos en la nube:** avisar claramente de que nombres de archivos y contenidos leídos pueden enviarse al proveedor; permitir excluir carpetas sensibles.
8. **Instrucciones dentro de archivos (prompt injection):** un archivo leído podría contener texto que intente manipular al modelo («borra todo»). Mitigación: el contenido de los archivos se trata como **datos**, y las acciones destructivas siempre exigen confirmación humana, sin excepciones ni «modo automático».
9. **Sin modo «autoaprobar» para borrados.** Si algún día se añade confianza automática, solo para acciones reversibles y de bajo riesgo (como crear una carpeta).

---

## 6. Fase 5 — Interfaz de chat

Objetivo: una ventana sencilla con un cuadro de texto, historial de conversación y diálogos de confirmación.

**Opciones de interfaz**

| Opción | Ventajas | Inconvenientes |
|---|---|---|
| **Tkinter** | Incluido en Python, ejecutable pequeño | Aspecto básico |
| **PySide6 / PyQt** | Aspecto profesional | Ejecutable más pesado; revisar licencia (LGPL/GPL) |
| **Web local (FastAPI) + ventana embebida** | Interfaz moderna | Más piezas que empaquetar |

Recomendación inicial: **Tkinter** para validar el producto; migrar solo si hace falta.

**Requisitos de la interfaz**

- Cuadro de entrada + área de conversación.
- Diálogo de confirmación con **ruta completa** y botones claros (*Confirmar* / *Cancelar*).
- Para lotes: lista desplazable con casillas para **desmarcar archivos concretos** antes de confirmar.
- Indicador de «trabajando…» y botón de cancelar.
- La IA se ejecuta en un **hilo aparte** para no congelar la ventana.
- Mensajes en lenguaje llano, no técnico.

---

## 7. Fase 6 — Segundo plano

- **Icono en la bandeja del sistema** (`pystray`) con menú: abrir chat, pausar, salir.
- **Vigilancia de carpetas** con `watchdog` para detectar archivos nuevos.
- **Cola de propuestas:** el vigilante *propone* («14 capturas nuevas») y el usuario decide. Nunca ejecuta cambios por su cuenta.
- **Bajo consumo:** no llamar al modelo por cada evento; agrupar eventos y actuar por lotes o con intervalos.
- **Una sola instancia:** evitar que se abran dos copias a la vez (archivo de bloqueo o *mutex*).
- **Inicio con el sistema** como opción, desactivada por defecto.
- **Notificaciones** no intrusivas, con límite de frecuencia.
- **Modo «no molestar»** y horarios configurables.

---

## 8. Fase 7 — Empaquetado como ejecutable

### Problemas conocidos en el código actual

1. **`herramientas.py`** calcula `RAIZ = Path(__file__).parent.parent`. En un ejecutable *onefile* esa ruta apunta a una carpeta temporal que se borra al cerrar. Los logs y el espacio de trabajo desaparecerían.
2. **`entorno.py`** fija `LOG = RAIZ / "logs" / ...` al importar, con el mismo problema.
3. **`cli.py`** usa `EQUIPO_POR_DEFECTO = "equipos/laboral.yaml"`, una ruta relativa al directorio actual.
4. **`loader.py`** necesita que los YAML estén incluidos en el paquete.

### Solución propuesta

Crear un módulo único `rutas.py`:

```python
import sys
from pathlib import Path

def recursos() -> Path:
    """Archivos de solo lectura incluidos en el ejecutable (YAML, iconos)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

def datos_usuario() -> Path:
    """Datos que deben persistir: configuración, logs, historial de deshacer."""
    base = Path.home() / ".mas"          # o %APPDATA%\MAS en Windows
    base.mkdir(parents=True, exist_ok=True)
    return base
```

- **Recursos** (YAML de plantillas, iconos) → `recursos()`.
- **Configuración, logs, historial** → `datos_usuario()`.
- Quitar el cálculo de rutas **en tiempo de importación**: pasarlas por parámetro o resolverlas al iniciar la aplicación.

### Pasos de empaquetado

1. Probar con `pyinstaller --onedir` primero (más fácil de depurar) y después `--onefile`.
2. `--windowed` para no abrir consola; en ese modo `print()` e `input()` no funcionan, razón de más para quitar la confirmación por consola.
3. Incluir datos con `--add-data` o un archivo `.spec`.
4. Declarar importaciones ocultas si PyInstaller no detecta módulos (`yaml`, el proveedor elegido, `pystray`).
5. Probar el `.exe` en una **máquina limpia** sin Python.
6. Aviso de antivirus y SmartScreen: los ejecutables sin firmar suelen generar alertas. Considerar firma de código y publicar sumas de verificación (SHA-256).
7. Automatizar con **CI** (GitHub Actions) para generar los binarios de cada sistema operativo; PyInstaller no compila de forma cruzada.
8. Alternativas si PyInstaller da problemas: **Nuitka** (más rápido, más lento de compilar) o **cx_Freeze**.
9. Estrategia de **actualizaciones** (aviso de nueva versión con enlace de descarga, como mínimo).

---

## 9. Correcciones técnicas del código actual

| Archivo | Problema | Propuesta |
|---|---|---|
| `result.py` | `ok()` hace `strip()` y altera el contenido (p. ej. indentación inicial). | Quitar el `strip()` del contrato o hacerlo opcional. |
| `orchestrator.py` | Reintenta cualquier fallo igual, incluso permanentes. | Distinguir errores transitorios y permanentes; añadir espera creciente. |
| `orchestrator.py` | `RECHAZADO`/`DENEGADO` de un paso se tratan como error genérico. | Propagar el estado real en el `Informe`. |
| `orchestrator.py` | El conteo `intentos` y `reintentos` confunde a la lectura. | Renombrar o comentar con un ejemplo. |
| `orchestrator.py` | El campo `orquestador:` del YAML no se usa. | Decidir: orquestador-LLM que delega, o cadena fija sin ese campo (ver §11). |
| `entorno.py` | `LOG`, `ESPACIO`, `RAIZ` se calculan al importar. | Pasarlos por parámetro desde un módulo de configuración. |
| `entorno.py` | `autorizar_por_consola` usa `input()`. | Interfaz `Autorizador` con varias implementaciones (§5.4). |
| `entorno.py` | `_auditar` trunca argumentos a 80 caracteres y podría filtrar secretos. | Rutas completas para acciones destructivas; enmascarar campos sensibles. |
| `entorno.py` | `Equipo` (modelo de datos) vive junto a la lógica de ejecución. | Moverlo a `teams/modelo.py` para evitar dependencias circulares. |
| `cli.py` | Todos los `--arg` llegan como `str`. | Convertir tipos según la firma de la herramienta; mensajes claros ante argumentos faltantes. |
| `cli.py` | `mas run` siempre usa el proveedor falso y un equipo distinto del YAML. | Construir agentes desde el YAML. |
| `loader.py` | Falla con `AttributeError` si un agente no es un diccionario o si `herramientas` es un texto. | Validar tipos y lanzar `ValueError` descriptivos. |
| `loader.py` | No valida campos nuevos (`prompt_sistema`, `proveedor`). | Ampliar esquema y validación. |
| `tools.py` | `REGISTRO` global y mutable; los tests dejan herramientas de prueba registradas. | Función para limpiar/aislar el registro en tests; o registro por instancia. |
| `tools.py` | No se comprueba que las herramientas que modifican algo declaren `requiere_confirmacion=True`. | Revisión en pruebas; valorar un nombre/categoría de riesgo (`lectura`, `escritura`, `destructiva`). |
| `herramientas.py` | `leer_archivo` sin límite de tamaño ni detección de binarios. | Límite configurable (p. ej. 1 MB) y error claro para binarios. |
| `herramientas.py` | `escribir_archivo` previsualiza solo bytes. | Indicar si sobrescribe, tamaño anterior y un *diff* resumido. |
| `__init__.py` | No exporta `Proveedor`, `ProveedorFalso` ni `cargar_equipo`; versión `0.3.0`. | Completar la API pública. |

---

## 10. Mejoras de tests

Los tests actuales son buenos (incluyen casos negativos). Faltan:

- **`cli.py`:** parseo de `--arg`, `_cmd_tool`, códigos de salida.
- **Bucle agente ↔ herramientas** (Fase 1), con el proveedor falso guionizado.
- **Integración:** petición → agente → herramienta → confirmación → archivo en disco, de principio a fin.
- **Enlaces simbólicos** que apunten fuera de la zona autorizada.
- **Sobrescritura** de un archivo existente y escritura en carpetas anidadas.
- **Herramientas nuevas:** borrar (a papelera, mockeando `send2trash`), mover (sin sobrescribir), lotes grandes, rutas protegidas.
- **Aislamiento del `REGISTRO`** entre tests.
- **Tests independientes de los YAML reales:** `test_entorno` carga `equipos/laboral.yaml`; si cambia el YAML se rompen pruebas de lógica. Usar YAML temporales.
- **Contexto no creciente entre reintentos.**
- **Pruebas del autorizador** con implementaciones simuladas (sin `input()`).
- **CI** que ejecute las pruebas en Windows, macOS y Linux.
- **Prueba de humo del ejecutable:** arrancar el `.exe` en CI y comprobar que responde (`--version`).

---

## 11. Decisiones pendientes

Cada una cambia el diseño; conviene decidirlas pronto:

1. **¿Orquestador-LLM o cadena fija?** Para un asistente de chat, lo natural es un **orquestador que interpreta la petición y delega** al agente adecuado (hoy solo existe una cadena lineal). Si el producto se simplifica a un único agente con herramientas, puede bastar con menos piezas.
2. **¿Cuántos agentes necesita realmente el producto?** Es posible que «organizador», «creador» y «limpiador» cubran todo; los roles `programador`/`analista` vienen del equipo `laboral` y quizá no encajen con la vida cotidiana.
3. **¿Nube, local o ambos?** Afecta a privacidad, coste y tamaño del ejecutable.
4. **¿Qué sistema operativo primero?** Se recomienda **Windows** primero (el empaquetado y la papelera difieren en cada sistema).
5. **¿Interfaz?** Tkinter para validar; decidir si se migra.
6. **¿Equipos distintos según el contexto?** Por ejemplo, perfiles «Trabajo» y «Personal» con carpetas y permisos distintos.
7. **Licencia y modelo de distribución** (gratuito, de pago, código abierto).
8. **Idioma:** el código y los YAML están en español; decidir si el producto será multilingüe.

---

## 12. Orden recomendado

| Orden | Fase | Resultado verificable |
|---|---|---|
| 1 | Correcciones rápidas (§9: `strip`, loader, registro en tests) | Tests en verde y más robustos |
| 2 | **Fase 1:** bucle agente ↔ herramientas | Test de integración con proveedor falso |
| 3 | Módulo `rutas.py` y configuración (§8) | Funciona igual en código y empaquetado |
| 4 | **Fase 2:** primer proveedor real + YAML completo | `mas run` hace trabajo real |
| 5 | **Fase 3:** herramientas (`borrar`, `mover`, `crear`, `organizar`) | Cada una con previsualización y tests |
| 6 | **Fase 4:** carpetas autorizadas y rutas protegidas | Pruebas de seguridad ampliadas |
| 7 | **Fase 5:** interfaz de chat con diálogos de confirmación | Se usa sin consola |
| 8 | **Primer ejecutable de prueba** (`--onedir`) | Funciona en una máquina limpia |
| 9 | **Fase 6:** bandeja del sistema y vigilancia | Funciona en segundo plano sin molestar |
| 10 | Firma, CI multiplataforma y actualizaciones | Versión distribuible |

> **Consejo:** genera un ejecutable de prueba **pronto** (paso 8, incluso con funciones mínimas). Los problemas de empaquetado se descubren tarde y cuestan caro si se acumulan.

---

## Dependencias previstas

| Librería | Para qué |
|---|---|
| `pyyaml` | Ya en uso (equipos YAML) |
| `send2trash` | Borrado a la papelera |
| `keyring` | Guardar claves de API de forma segura |
| `watchdog` | Vigilar carpetas |
| `pystray` + `Pillow` | Icono en la bandeja del sistema |
| `anthropic` / `openai` / cliente de Ollama | Proveedor de IA (según decisión) |
| `pyinstaller` | Empaquetado |
| `pytest` (opcional) | Pruebas más cómodas |
