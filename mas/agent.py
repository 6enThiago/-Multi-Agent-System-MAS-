"""Agente: una sola responsabilidad.

Principio: "Un agente, una responsabilidad".
Un agente hace una cosa bien y nunca habla con otro agente directamente:
toda coordinación la hace el orquestador.
"""
from __future__ import annotations

from dataclasses import dataclass

from .providers import Proveedor
from .result import ResultadoAgente


@dataclass
class Agente:
    """Unidad autónoma con un rol único y un proveedor de modelos."""

    id: str
    rol: str
    prompt_sistema: str
    proveedor: Proveedor

    def ejecutar(self, tarea: str, contexto: str = "") -> ResultadoAgente:
        """Ejecuta su única responsabilidad.

        Recibe solo contexto mínimo (nunca la conversación completa)
        y **nunca lanza excepciones**: todo error vuelve dentro del
        contrato estandarizado.
        """
        try:
            entrada = f"Tarea: {tarea}"
            if contexto:
                entrada = f"Contexto previo:\n{contexto}\n\n{entrada}"
            salida = self.proveedor.completar(entrada, sistema=self.prompt_sistema)
            return ResultadoAgente.ok(salida)
        except Exception as exc:  # el contrato captura todo, sin excepciones
            return ResultadoAgente.fallido(f"{type(exc).__name__}: {exc}")
