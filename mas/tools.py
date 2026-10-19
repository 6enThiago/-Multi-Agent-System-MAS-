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
from typing import Callable


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
