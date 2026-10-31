"""Orquestador central.

Principios: "Orquestador al centro" y "Contexto mínimo".
Los agentes no se hablan entre sí: el orquestador ejecuta la cadena y
les pasa únicamente la salida del paso anterior.

Cuando un paso devuelve ``RECHAZADO`` o ``DENEGADO``, ese estado se
propaga tal cual en el ``Informe`` (no se convierte en un error
genérico): el usuario o el agente siguiente pueden decidir qué hacer.
Solo un ``ERROR`` de verdad detiene la cadena.
"""
from __future__ import annotations

from .agent import Agente
from .result import Estado, ResultadoAgente

# Estados que, aunque no sean "ok", no se consideran fallos irrecuperables
# que deban detener la cadena con un ERROR genérico.
ESTADOS_NO_ERROR = {Estado.OK, Estado.RECHAZADO, Estado.DENEGADO}


class PasoEjecutado:
    """Traza de un paso: qué agente corrió, con cuántos intentos y qué salió."""

    __slots__ = ("agente_id", "intentos_usados", "resultado")

    def __init__(self, agente_id: str, intentos_usados: int, resultado: ResultadoAgente) -> None:
        self.agente_id = agente_id
        self.intentos_usados = intentos_usados
        self.resultado = resultado

    def a_dict(self) -> dict:
        return {
            "agente": self.agente_id,
            "intentos": self.intentos_usados,
            **self.resultado.a_dict(),
        }


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

    def __init__(self, reintentos_maximos: int = 1) -> None:
        if reintentos_maximos < 0:
            raise ValueError("reintentos_maximos no puede ser negativo")
        self.reintentos_maximos = reintentos_maximos

    def ejecutar(self, tarea: str, agentes: list[Agente]) -> Informe:
        """Ejecuta la cadena completa para una tarea.

        Devuelve siempre un `Informe` estandarizado; nunca lanza por
        fallos de agentes (solo por uso incorrecto de la API).

        Reintentos: el primer intento cuenta como 1; si el resultado no
        es ok se reintenta hasta llegar a ``1 + reintentos_maximos``
        intentos totales.
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
            intentos_usados = 1
            while (
                resultado.estado not in ESTADOS_NO_ERROR
                and intentos_usados <= self.reintentos_maximos
            ):
                intentos_usados += 1
                resultado = agente.ejecutar(tarea, contexto)
            pasos.append(PasoEjecutado(agente.id, intentos_usados, resultado))

            if resultado.estado not in ESTADOS_NO_ERROR:
                # Cadena detenida: un ERROR de verdad no se continúa.
                return Informe(
                    Estado.ERROR,
                    "",
                    tuple(f"Falló el agente '{agente.id}': {e}" for e in resultado.errores),
                    tuple(pasos),
                )

            contexto = resultado.resultado  # el siguiente agente recibe solo esto

        # El estado final es el del último paso (puede ser ok / rechazado / denegado).
        ultimo = pasos[-1]
        return Informe(ultimo.resultado.estado, ultimo.resultado.resultado, ultimo.resultado.errores, tuple(pasos))
