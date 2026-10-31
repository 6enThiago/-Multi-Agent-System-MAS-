"""Contrato de salida estandarizado del MAS.

Principio: "Salidas estandarizadas".
Todo agente y todo informe del orquestador devuelven exactamente
este formato: estado, resultado, errores. Nada más.
"""
from __future__ import annotations

from enum import Enum


class Estado(str, Enum):
    """Estado posible de cualquier resultado."""

    OK = "ok"
    RECHAZADO = "rechazado"  # el humano negó la confirmación
    DENEGADO = "denegado"    # el agente no tiene permiso en su YAML
    ERROR = "error"


class ResultadoAgente:
    """Salida única y uniforme de un agente (inmutable por diseño)."""

    __slots__ = ("estado", "resultado", "errores")

    def __init__(self, estado: Estado, resultado: str, errores: tuple[str, ...] = ()) -> None:
        object.__setattr__(self, "estado", estado)
        object.__setattr__(self, "resultado", resultado)
        object.__setattr__(self, "errores", tuple(errores))

    def __setattr__(self, nombre: str, valor: object) -> None:  # inmutable
        raise AttributeError("ResultadoAgente es inmutable; crea uno nuevo")

    @classmethod
    def ok(cls, resultado: str) -> "ResultadoAgente":
        """Crea un resultado exitoso (el texto se devuelve tal cual, sin alterarlo)."""
        return cls(Estado.OK, resultado)

    @classmethod
    def fallido(cls, *errores: str) -> "ResultadoAgente":
        """Crea un resultado fallido con uno o más mensajes de error."""
        return cls(Estado.ERROR, "", tuple(errores))

    @classmethod
    def rechazado(cls, previa: str, *errores: str) -> "ResultadoAgente":
        """Acción que el humano negó. `previa` conserva qué se rechazó."""
        return cls(Estado.RECHAZADO, previa, tuple(errores))

    @classmethod
    def denegado(cls, *errores: str) -> "ResultadoAgente":
        """Acción que el agente no tiene permiso para realizar."""
        return cls(Estado.DENEGADO, "", tuple(errores))

    @property
    def es_ok(self) -> bool:
        return self.estado is Estado.OK

    def a_dict(self) -> dict:
        """Representación JSON-ready y estandarizada."""
        return {
            "estado": self.estado.value,
            "resultado": self.resultado,
            "errores": list(self.errores),
        }

    def __repr__(self) -> str:
        return f"ResultadoAgente(estado={self.estado.value!r}, resultado={self.resultado!r}, errores={self.errores!r})"
