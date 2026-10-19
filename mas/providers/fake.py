"""Proveedor falso: determinista, sin red ni claves de API.

Principio: "Todo verificable". Permite ejecutar y probar el pipeline
completo de punta a punta con coste cero.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProveedorFalso:
    """Proveedor determinista para tests y demostraciones.

    - ``guion``: respuestas pregrabadas que se consumen en orden; al
      agotarse, hace eco de la entrada.
    - ``excepcion``: si se indica, toda llamada la lanza (simula fallos).
    - ``llamadas``: traza de (sistema, entrada) para poder asertar en tests.
    """

    guion: list[str] | None = None
    excepcion: Exception | None = None
    llamadas: list[tuple[str, str]] = field(default_factory=list)

    def completar(self, entrada: str, *, sistema: str) -> str:
        self.llamadas.append((sistema, entrada))
        if self.excepcion is not None:
            raise self.excepcion
        if self.guion:
            return self.guion.pop(0)
        return f"[{sistema}] {entrada}"
