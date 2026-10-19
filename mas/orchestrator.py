"""Orquestador central.

Principios: "Orquestador al centro" y "Contexto mínimo".
Los agentes no se hablan entre sí: el orquestador ejecuta la cadena y
les pasa únicamente la salida del paso anterior. Si un paso falla tras
reintentarlo, la cadena se detiene y se reporta.
"""
from __future__ import annotations

from .agent import Agente
from .result import Estado, ResultadoAgente


class PasoEjecutado:
    """Traza de un paso: qué agente corrió, con cuántos intentos y qué salió."""

    __slots__ = ("agente_id", "intentos", "resultado")

    def __init__(self, agente_id: str, intentos: int, resultado: ResultadoAgente) -> None:
        self.agente_id = agente_id
        self.intentos = intentos
        self.resultado = resultado

    def a_dict(self) -> dict:
        return {"agente": self.agente_id, "intentos": self.intentos, **self.resultado.a_dict()}


class Informe:
    """Resultado estandarizado de toda ejecución del orquestador."""

    __slots__ = ("estado", "resultado", "errores", "pasos")

    def __init__(
        self,
        estado: Estado,
        resultado: str,
        errores: tuple[str, ...],
        pasos: tuple[PasoEjecutado, ...],
    ) -> None:
        self.estado = estado
        self.resultado = resultado
        self.errores = tuple(errores)
        self.pasos = tuple(pasos)

    @property
    def es_ok(self) -> bool:
        return self.estado is Estado.OK

    def a_dict(self) -> dict:
        """Mismo contrato que un agente, más la traza de pasos."""
        return {
            "estado": self.estado.value,
            "resultado": self.resultado,
            "errores": list(self.errores),
            "pasos": [p.a_dict() for p in self.pasos],
        }


class Orquestador:
    """Secuencia los agentes en cadena con reintentos limitados."""

    def __init__(self, reintentos: int = 1) -> None:
        if reintentos < 0:
            raise ValueError("reintentos no puede ser negativo")
        self.reintentos = reintentos

    def ejecutar(self, tarea: str, agentes: list[Agente]) -> Informe:
        """Ejecuta la cadena completa para una tarea.

        Devuelve siempre un `Informe` estandarizado; nunca lanza por
        fallos de agentes (solo por uso incorrecto de la API).
        """
        if not agentes:
            return Informe(
                Estado.ERROR,
                "",
                ("El equipo está vacío: no hay agentes que ejecutar.",),
                (),
            )

        pasos: list[PasoEjecutado] = []
        contexto = ""  # contexto mínimo: solo la salida del paso anterior

        for agente in agentes:
            resultado = agente.ejecutar(tarea, contexto)
            intentos = 1
            while not resultado.es_ok and intentos <= self.reintentos:
                intentos += 1
                resultado = agente.ejecutar(tarea, contexto)
            pasos.append(PasoEjecutado(agente.id, intentos, resultado))

            if not resultado.es_ok:
                # Cadena detenida: no se continúa si un paso crítico falló.
                return Informe(
                    Estado.ERROR,
                    "",
                    tuple(f"Falló el agente '{agente.id}': {e}" for e in resultado.errores),
                    tuple(pasos),
                )

            contexto = resultado.resultado  # el siguiente agente recibe solo esto

        return Informe(Estado.OK, pasos[-1].resultado.resultado, (), tuple(pasos))
