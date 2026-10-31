"""Herramientas de ejemplo: lectura y escritura de archivos.

Seguridad por diseño: todas las rutas se resuelven dentro del área de
trabajo (raíz) del entorno. Cualquier intento de escapar
(``../../etc/passwd``) se bloquea con estado error, sin tocar el disco.

Siguen la regla de oro: la firma declara ``confirmar=False``; la
escritura real solo ocurre con ``confirmar=True``.
"""
from __future__ import annotations

import datetime
import difflib
import hashlib
from pathlib import Path

import send2trash

from .tools import herramienta

RAIZ = Path(__file__).resolve().parent.parent  # raíz del proyecto
ESPACIO = (RAIZ / "espacio_trabajo").resolve()  # área de trabajo de los agentes

# Límite de lectura por archivo (1 MB). Evita cargar archivos enormes en memoria.
LIMITE_TAMANIO_BYTES = 1024 * 1024


class ErrorRutaIlegal(RuntimeError):
    """La ruta intenta salirse del área de trabajo."""


class ErrorArchivoBinario(RuntimeError):
    """El archivo parece binario y no se lee como texto."""


def _resolver(ruta: str, raiz: Path | None) -> Path:
    """Resuelve `ruta` dentro de la raíz; lanza ErrorRutaIlegal si escapa."""
    base = (raiz or ESPACIO).resolve()
    destino = (base / ruta).resolve()
    if not destino.is_relative_to(base):
        raise ErrorRutaIlegal(f"Ruta bloqueada: '{ruta}' está fuera del área de trabajo.")
    return destino


def _tamano(destino: Path) -> int:
    """Devuelve el tamaño en bytes del archivo, o 0 si no existe."""
    try:
        return destino.stat().st_size
    except OSError:
        return 0


def _es_binario(contenido_bytes: bytes) -> bool:
    """Heurística simple: un byte nulo indica archivo binario."""
    return b"\x00" in contenido_bytes


def _diff_resumido(antes: str, despues: str, max_lineas: int = 15) -> str:
    """Devuelve un diff resumido (unificado) entre dos textos."""
    lineas_antes = antes.splitlines(keepends=True)
    lineas_despues = despues.splitlines(keepends=True)
    diferencias = list(
        difflib.unified_diff(lineas_antes, lineas_despues, lineterm="", n=2)
    )
    if not diferencias:
        return "(sin cambios de texto)"
    lineas_diff = [l for l in diferencias if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    if not lineas_diff:
        return "(sin cambios de texto)"
    seleccion = lineas_diff[:max_lineas]
    sobran = len(lineas_diff) - len(seleccion)
    texto = "\n".join(seleccion)
    if sobran > 0:
        texto += f"\n... y {sobran} línea(s) más"
    return texto


@herramienta("leer_archivo", requiere_confirmacion=False)
def leer_archivo(ruta: str, *, raiz: Path | None = None, confirmar: bool = False) -> str:
    """Lee un archivo de texto dentro del área de trabajo. No pide confirmación."""
    destino = _resolver(ruta, raiz)
    if not destino.is_file():
        raise FileNotFoundError(f"No existe el archivo: '{ruta}'")

    tamano = destino.stat().st_size
    if tamano > LIMITE_TAMANIO_BYTES:
        raise ErrorArchivoBinario(
            f"El archivo '{ruta}' ({tamano} bytes) supera el límite de lectura "
            f"({LIMITE_TAMANIO_BYTES} bytes)."
        )

    datos = destino.read_bytes()
    if _es_binario(datos):
        raise ErrorArchivoBinario(f"El archivo '{ruta}' parece binario y no se lee como texto.")

    texto = datos.decode("utf-8")
    return f"--- {ruta} ({tamano} bytes) ---\n{texto}"


@herramienta("escribir_archivo", requiere_confirmacion=True)
def escribir_archivo(
    ruta: str, contenido: str, *, raiz: Path | None = None, confirmar: bool = False
) -> str:
    """Sobrescribe un archivo de texto. Con confirmar=False solo previsualiza."""
    destino = _resolver(ruta, raiz)
    existe = destino.is_file()
    tamano_anterior = _tamano(destino)
    contenido_bytes = contenido.encode("utf-8")
    tamano_nuevo = len(contenido_bytes)

    if not confirmar:
        # Regla de oro: primero la previsualización (confirmar=False).
        lineas = [
            f"PREVISUALIZACIÓN: escribiría '{ruta}' ({tamano_nuevo} bytes).",
        ]
        if existe:
            lineas.append(f"  El archivo ya existe (tamaño anterior: {tamano_anterior} bytes) y se SOBRESCRIBIRÍA.")
            if tamano_anterior > 0:
                try:
                    antes = destino.read_text(encoding="utf-8")
                    lineas.append("  Diff resumido:")
                    lineas.append("    " + _diff_resumido(antes, contenido).replace("\n", "\n    "))
                except (OSError, UnicodeDecodeError):
                    lineas.append("  (no se pudo generar diff: el archivo actual no es texto legible)")
        else:
            lineas.append("  El archivo no existe; se creará nuevo.")
        return "\n".join(lineas)

    # Proceso real: solo con confirmar=True (tras autorización).
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    verbo = "sobrescrito" if existe else "creado"
    return f"{verbo.capitalize()} '{ruta}' ({tamano_anterior} → {tamano_nuevo} bytes)."


# ---------------------------------------------------------------------------
# Herramientas de producto (Fase 3)
# ---------------------------------------------------------------------------

@herramienta("listar_carpeta", requiere_confirmacion=False)
def listar_carpeta(
    ruta: str = ".",
    *,
    raiz: Path | None = None,
    confirmar: bool = False,
    limite: int = 100,
) -> str:
    """Lista archivos de una carpeta con tamaño y fecha de modificación."""
    destino = _resolver(ruta, raiz)
    if not destino.is_dir():
        raise NotADirectoryError(f"No existe la carpeta: '{ruta}'")

    entradas = []
    for entrada in sorted(destino.iterdir()):
        try:
            stat = entrada.stat()
            tamano = stat.st_size
            fecha = datetime.datetime.fromtimestamp(stat.st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )
            tipo = "dir" if entrada.is_dir() else "file"
            entradas.append((tipo, fecha, tamano, entrada.name))
        except OSError:
            continue

    if len(entradas) > limite:
        entradas = entradas[:limite]
        truncado = f"\n... (mostrando las primeras {limite} de más entradas)"
    else:
        truncado = ""

    lineas = [f"--- Carpeta: {ruta} ({len(entradas)} entrada(s)) ---"]
    for tipo, fecha, tamano, nombre in entradas:
        marca = "/" if tipo == "dir" else " "
        lineas.append(f"  {marca} {fecha:16} {tamano:>10} bytes  {nombre}")
    lineas.append(truncado)
    return "\n".join(lineas)


@herramienta("crear_carpeta", requiere_confirmacion=True)
def crear_carpeta(
    ruta: str, *, raiz: Path | None = None, confirmar: bool = False
) -> str:
    """Crea una carpeta (incluyendo padres). Con confirmar=False solo previsualiza."""
    destino = _resolver(ruta, raiz)
    if not confirmar:
        ya_existe = destino.exists()
        return (
            f"PREVISUALIZACIÓN: crearía la carpeta '{ruta}'."
            + (f" (YA EXISTE)" if ya_existe else "")
        )
    destino.mkdir(parents=True, exist_ok=True)
    return f"Carpeta creada: '{ruta}'."


@herramienta("mover_archivo", requiere_confirmacion=True)
def mover_archivo(
    origen: str, destino_nuevo: str, *, raiz: Path | None = None, confirmar: bool = False
) -> str:
    """Mueve/renombra un archivo. No sobrescribe sin aviso."""
    origen_resuelto = _resolver(origen, raiz)
    destino_resuelto = _resolver(destino_nuevo, raiz)

    if not origen_resuelto.exists():
        raise FileNotFoundError(f"No existe el archivo de origen: '{origen}'")
    if destino_resuelto.exists():
        raise FileExistsError(
            f"El destino ya existe: '{destino_nuevo}'. No se sobrescribe sin aviso."
        )

    if not confirmar:
        tamano = origen_resuelto.stat().st_size
        return (
            f"PREVISUALIZACIÓN: movería '{origen}' → '{destino_nuevo}' "
            f"({tamano} bytes)."
        )

    destino_resuelto.parent.mkdir(parents=True, exist_ok=True)
    origen_resuelto.rename(destino_resuelto)
    return f"Movido '{origen}' → '{destino_nuevo}'."


_LIMITE_LOTE_BORRADO = 25


@herramienta("borrar_archivo", requiere_confirmacion=True)
def borrar_archivo(
    rutas: str | list[str],
    *,
    raiz: Path | None = None,
    confirmar: bool = False,
    permanente: bool = False,
) -> str:
    """Envía archivos a la papelera (send2trash). Borrado permanente solo con permanente=True.

    `rutas` puede ser una ruta o una lista de rutas. Con confirmar=False solo previsualiza.
    """
    if isinstance(rutas, str):
        rutas = [rutas]

    resoluidas = []
    for ruta in rutas:
        destino = _resolver(ruta, raiz)
        if not destino.exists():
            raise FileNotFoundError(f"No existe: '{ruta}'")
        # No permitir borrar la raíz misma ni rutas protegidas por nombre.
        if destino == (raiz or ESPACIO).resolve():
            raise ErrorRutaIlegal(f"No se puede borrar la raíz del área de trabajo: '{ruta}'")
        resoluidas.append(destino)

    total = len(resoluidas)
    detalle = []
    for destino in resoluidas:
        stat = destino.stat()
        tamano = stat.st_size
        fecha = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        detalle.append(f"  - {destino} ({tamano} bytes, modificado {fecha})")

    if not confirmar:
        lineas = [
            f"PREVISUALIZACIÓN: {'enviaría a la papelera' if not permanente else 'borraría permanentemente'} {total} archivo(s):",
        ]
        lineas.extend(detalle)
        if total > _LIMITE_LOTE_BORRADO:
            lineas.append(
                f"  ATENCIÓN: lote de {total} archivos supera el límite de {_LIMITE_LOTE_BORRADO}; se recomienda una segunda confirmación."
            )
        return "\n".join(lineas)

    borrados = []
    for destino in resoluidas:
        if permanente:
            destino.unlink()
        else:
            send2trash.send2trash(str(destino))
        borrados.append(str(destino))

    destino_str = "permanentemente" if permanente else "a la papelera"
    return f"{total} archivo(s) {destino_str}: " + ", ".join(borrados)


@herramienta("buscar_duplicados", requiere_confirmacion=False)
def buscar_duplicados(
    ruta: str = ".", *, raiz: Path | None = None, confirmar: bool = False
) -> str:
    """Detecta archivos idénticos por hash (SHA-256). Solo lista; no borra."""
    destino = _resolver(ruta, raiz)
    if not destino.is_dir():
        raise NotADirectoryError(f"No existe la carpeta: '{ruta}'")

    hashes: dict[str, list[Path]] = {}
    for archivo in destino.rglob("*"):
        if not archivo.is_file():
            continue
        try:
            h = hashlib.sha256(archivo.read_bytes()).hexdigest()
        except OSError:
            continue
        hashes.setdefault(h, []).append(archivo)

    duplicados = {h: caminos for h, caminos in hashes.items() if len(caminos) > 1}

    if not duplicados:
        return f"--- No se encontraron duplicados en '{ruta}' ---"

    lineas = [f"--- Duplicados en '{ruta}' ---"]
    for caminos in duplicados.values():
        lineas.append("")
        for c in caminos:
            tamano = c.stat().st_size
            lineas.append(f"  {c} ({tamano} bytes)")
    return "\n".join(lineas)


@herramienta("organizar_carpeta", requiere_confirmacion=True)
def organizar_carpeta(
    ruta: str = ".", *, raiz: Path | None = None, confirmar: bool = False
) -> str:
    """Propone un plan de movimientos por tipo de archivo. No ejecuta nada hasta confirmar=True."""
    destino = _resolver(ruta, raiz)
    if not destino.is_dir():
        raise NotADirectoryError(f"No existe la carpeta: '{ruta}'")

    # Agrupar archivos por extensión.
    grupos: dict[str, list[Path]] = {}
    for archivo in destino.iterdir():
        if not archivo.is_file():
            continue
        ext = archivo.suffix.lower() or "sin_extension"
        grupos.setdefault(ext, []).append(archivo)

    if not grupos:
        return f"--- No hay archivos que organizar en '{ruta}' ---"

    lineas = [f"--- Plan de organización para '{ruta}' ---"]
    total_movimientos = 0
    for ext, archivos in sorted(grupos.items()):
        carpeta_destino = destino / ext.lstrip(".")
        lineas.append(f"  → carpeta '{ext.lstrip('.')}/': {len(archivos)} archivo(s)")
        for a in archivos:
            lineas.append(f"      '{a.name}'")
        total_movimientos += len(archivos)

    lineas.append("")
    lineas.append(f"Total de movimientos propuestos: {total_movimientos}")
    lineas.append("Con confirmar=True se ejecutarán todos los movimientos de este plan.")

    if not confirmar:
        return "\n".join(lineas)

    # Ejecutar el plan.
    realizados = 0
    for ext, archivos in grupos.items():
        carpeta_destino = destino / ext.lstrip(".")
        carpeta_destino.mkdir(exist_ok=True)
        for archivo in archivos:
            nuevo = carpeta_destino / archivo.name
            if nuevo.exists():
                continue  # no sobrescribir
            archivo.rename(nuevo)
            realizados += 1

    return f"Organización completada: {realizados} archivo(s) movido(s) en '{ruta}'."
