"""Adaptadores de modelos (proveedores)."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Proveedor(Protocol):
    """Contrato mínimo de un proveedor de modelos.

    Cualquier backend (OpenAI, Anthropic, Ollama, falso…) debe poder
    sustituirse sin tocar el resto del sistema.
    """

    def completar(self, entrada: str, *, sistema: str) -> str:
        """Devuelve la respuesta en texto.

        Puede lanzar una excepción: el agente la captura y la convierte
        en el contrato de error.
        """
        ...
