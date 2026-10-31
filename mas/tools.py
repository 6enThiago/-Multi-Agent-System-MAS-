"""Registro de herramientas y su decorador.

Regla de oro del proyecto: toda función que se agregue como herramienta
se escribe primero con ``confirmar=False`` (valor por defecto de su
firma); los procesos que modifican el entorno corren con
``confirmar=True`` únicamente tras la autorización. El decorador lo
exige mecánicamente: una función sin ese parámetro no se registra.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, get_type_hints


@dataclass(frozen=True)
class Herramienta:
    """Metadatos de una herramienta registrada."""

    nombre: str
    funcion: Callable
    requiere_confirmacion: bool
    descripcion: str


REGISTRO: dict[str, Herramienta] = {}


def herramienta(nombre: str | None = None, *, requiere_confirmacion: bool = False):
    """Registra una función como herramienta usable por los agentes.

    - ``requiere_confirmacion=False``: se ejecuta sola (ej. lecturas).
    - ``requiere_confirmacion=True``: previsualiza con ``confirmar=False``
      y solo se ejecuta con ``confirmar=True`` tras autorización humana.
    """

    def decorador(func: Callable) -> Callable:
        nombre_final = nombre or func.__name__
        parametros = inspect.signature(func).parameters

        if "confirmar" not in parametros:
            raise TypeError(
                f"Herramienta '{nombre_final}': la regla de oro exige declarar el parámetro 'confirmar' (default False)."
            )
        if parametros["confirmar"].default is not False:
            raise TypeError(
                f"Herramienta '{nombre_final}': 'confirmar' debe tener como valor por defecto False."
            )
        if nombre_final in REGISTRO:
            raise ValueError(f"Herramienta duplicada: '{nombre_final}'")

        REGISTRO[nombre_final] = Herramienta(
            nombre=nombre_final,
            funcion=func,
            requiere_confirmacion=requiere_confirmacion,
            descripcion=inspect.getdoc(func) or "",
        )
        return func

    return decorador


def obtener(nombre: str) -> Herramienta | None:
    """Busca una herramienta por nombre; None si no existe."""
    return REGISTRO.get(nombre)


def limpiar_registro() -> None:
    """Elimina todas las herramientas registradas.

    Útil en tests para aislar el registro global entre pruebas y evitar
    que una herramienta de prueba afecte a otra.
    """
    REGISTRO.clear()


def _tipo_de_parametro(anotacion: object) -> str:
    """Devuelve una representación legible del tipo de un parámetro."""
    if anotacion is inspect.Parameter.empty:
        return "desconocido"
    # get_type_hints ya resuelve forward references; si aún llega como str,
    # lo tratamos manualmente (por compatibilidad con versiones antiguas).
    if isinstance(anotacion, str):
        if anotacion == "str":
            return "texto"
        if anotacion == "int":
            return "entero"
        if anotacion == "bool":
            return "booleano"
        if "Path" in anotacion:
            return "ruta"
        return anotacion
    if anotacion is str:
        return "texto"
    if anotacion is int:
        return "entero"
    if anotacion is bool:
        return "booleano"
    if anotacion is Path:
        return "ruta"
    # Tipos genéricos como Optional[Path], list[str], etc.
    nombre = getattr(anotacion, "__name__", None)
    if nombre:
        return nombre
    return str(anotacion)


def esquema_de(nombre: str) -> dict | None:
    """Devuelve el esquema de una herramienta para describírselo al modelo.

    Estructura::

        {
          "nombre": "leer_archivo",
          "requiere_confirmacion": False,
          "descripcion": "...",
          "parametros": {
            "ruta": {"tipo": "texto", "obligatorio": True, "descripcion": "..."},
            ...
          }
        }

    Devuelve None si la herramienta no existe.
    """
    herramienta = obtener(nombre)
    if herramienta is None:
        return None

    # get_type_hints resuelve las anotaciones incluso con
    # ``from __future__ import annotations`` (que las deja como strings).
    try:
        tipo_hints = get_type_hints(herramienta.funcion)
    except (NameError, AttributeError):
        tipo_hints = {}

    firma = inspect.signature(herramienta.funcion)
    parametros: dict[str, dict] = {}
    for nombre_param, parametro in firma.parameters.items():
        if nombre_param in ("raiz", "confirmar"):
            continue  # son inyectados por el entorno, no se los pasa el modelo
        obligatorio = parametro.default is inspect.Parameter.empty
        anotacion = tipo_hints.get(nombre_param, parametro.annotation)
        parametros[nombre_param] = {
            "tipo": _tipo_de_parametro(anotacion),
            "obligatorio": obligatorio,
            "descripcion": "",
        }

    return {
        "nombre": herramienta.nombre,
        "requiere_confirmacion": herramienta.requiere_confirmacion,
        "descripcion": herramienta.descripcion,
        "parametros": parametros,
    }


def listar_esquemas(nombres: list[str] | None = None) -> list[dict]:
    """Devuelve los esquemas de las herramientas indicadas (o de todas)."""
    if nombres is None:
        nombres = sorted(REGISTRO)
    esquemas = []
    for nombre in nombres:
        esquema = esquema_de(nombre)
        if esquema is not None:
            esquemas.append(esquema)
    return esquemas
