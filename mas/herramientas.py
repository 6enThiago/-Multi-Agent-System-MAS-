"""Herramientas de ejemplo: lectura y escritura de archivos.

Seguridad por diseño: todas las rutas se resuelven dentro del área de
trabajo (raíz) del entorno. Cualquier intento de escapar
(``../../etc/passwd``) se bloquea con estado error, sin tocar el disco.

Siguen la regla de oro: la firma declara ``confirmar=False``; la
escritura real solo ocurre con ``confirmar=True``.
"""
from __future__ import annotations

from pathlib import Path

from .tools import herramienta

RAIZ = Path(__file__).resolve().parent.parent  # raíz del proyecto
ESPACIO = (RAIZ / "espacio_trabajo").resolve()  # área de trabajo de los agentes


class ErrorRutaIlegal(RuntimeError):
    """La ruta intenta salirse del área de trabajo."""


def _resolver(ruta: str, raiz: Path | None) -> Path:
    """Resuelve `ruta` dentro de la raíz; lanza ErrorRutaIlegal si escapa."""
    base = (raiz or ESPACIO).resolve()
    destino = (base / ruta).resolve()
    if not destino.is_relative_to(base):
        raise ErrorRutaIlegal(f"Ruta bloqueada: '{ruta}' está fuera del área de trabajo.")
    return destino


@herramienta("leer_archivo", requiere_confirmacion=False)
def leer_archivo(ruta: str, *, raiz: Path | None = None, confirmar: bool = False) -> str:
    """Lee un archivo de texto dentro del área de trabajo. No pide confirmación."""
    destino = _resolver(ruta, raiz)
    if not destino.is_file():
        raise FileNotFoundError(f"No existe el archivo: '{ruta}'")
    texto = destino.read_text(encoding="utf-8")
    return f"--- {ruta} ({len(texto.encode('utf-8'))} bytes) ---\n{texto}"


@herramienta("escribir_archivo", requiere_confirmacion=True)
def escribir_archivo(
    ruta: str, contenido: str, *, raiz: Path | None = None, confirmar: bool = False
) -> str:
    """Sobrescribe un archivo de texto. Con confirmar=False solo previsualiza."""
    destino = _resolver(ruta, raiz)
    if not confirmar:
        # Regla de oro: primero la previsualización (confirmar=False).
        return f"PREVISUALIZACIÓN: escribiría '{ruta}' ({len(contenido.encode('utf-8'))} bytes)."
    # Proceso real: solo con confirmar=True (tras autorización).
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    return f"Escrito '{ruta}' ({len(contenido.encode('utf-8'))} bytes)."
