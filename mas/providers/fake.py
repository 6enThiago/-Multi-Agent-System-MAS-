"""Proveedor falso: determinista, sin red ni claves de API.

Principio: "Todo verificable". Permite ejecutar y probar el pipeline
completo de punta a punta con coste cero.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import LlamadaHerramienta, RespuestaModelo


@dataclass
class ProveedorFalso:
    """Proveedor determinista para tests y demostraciones.

    - ``guion``: respuestas pregrabadas que se consumen en orden; cada
      elemento puede ser un ``str`` (se envuelve como texto) o una
      :class:`RespuestaModelo`. Al agotarse, hace eco de la entrada.
    - ``excepcion``: si se indica, toda llamada la lanza (simula fallos).
    - ``llamadas``: traza de (sistema, entrada) para poder asertar en tests.
    """

    guion: list[str | RespuestaModelo] | None = None
    excepcion: Exception | None = None
    llamadas: list[tuple[str, str]] = field(default_factory=list)

    def _envolver(self, respuesta: str | RespuestaModelo) -> RespuestaModelo:
        if isinstance(respuesta, RespuestaModelo):
            return respuesta
        return RespuestaModelo(texto=respuesta)

    def completar(self, entrada: str, *, sistema: str) -> RespuestaModelo:
        self.llamadas.append((sistema, entrada))
        if self.excepcion is not None:
            raise self.excepcion
        if self.guion:
            return self._envolver(self.guion.pop(0))
        return RespuestaModelo(texto=f"[{sistema}] {entrada}")
