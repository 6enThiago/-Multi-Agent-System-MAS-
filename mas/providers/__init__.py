"""Adaptadores de modelos (proveedores)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LlamadaHerramienta:
    """Petición del modelo para ejecutar una herramienta."""

    nombre: str
    argumentos: dict


@dataclass(frozen=True)
class RespuestaModelo:
    """Respuesta de un proveedor: texto final y/o una petición de herramienta."""

    texto: str = ""
    llamada: LlamadaHerramienta | None = None


@runtime_checkable
class Proveedor(Protocol):
    """Contrato mínimo de un proveedor de modelos.

    Cualquier backend (OpenAI, Anthropic, Ollama, falso…) debe poder
    sustituirse sin tocar el resto del sistema.

    ``completar`` devuelve una :class:`RespuestaModelo`: puede contener
    solo ``texto`` (respuesta final), solo ``llamada`` (el modelo pide
    ejecutar una herramienta) o ambas.
    """

    def completar(self, entrada: str, *, sistema: str) -> RespuestaModelo:
        """Devuelve la respuesta del modelo.

        Puede lanzar una excepción: el agente la captura y la convierte
        en el contrato de error.
        """
        ...
