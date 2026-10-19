"""Entorno: la única puerta entre los agentes y el sistema de archivos.

Sistema unificado tras la convergencia `mas/` + `core/`:

- permisos por equipo (YAML en ``equipos/``)
- previsualización con ``confirmar=False`` antes de preguntar (regla de oro)
- autorización humana (consola por defecto) → proceso real con ``confirmar=True``
- auditoría de cada ejecución en ``logs/herramientas.jsonl``
- bloqueo de rutas fuera del área de trabajo (``espacio_trabajo/``)

Estados: ok / rechazado / denegado / error.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .herramientas import ESPACIO, RAIZ, ErrorRutaIlegal
from .result import Estado, ResultadoAgente
from .tools import obtener

LOG = RAIZ / "logs" / "herramientas.jsonl"

# Recibe la previsualización (texto) y devuelve True si el humano autoriza.
Autorizacion = Callable[[str], bool]


@dataclass(frozen=True)
class Equipo:
    """Equipo cargado desde YAML: identidad, orquestador y permisos por agente."""

    nombre: str
    descripcion: str
    orquestador: str
    permisos: dict[str, tuple[str, ...]]

    @property
    def agentes(self) -> tuple[str, ...]:
        return tuple(self.permisos)

    def herramientas_de(self, agente_id: str) -> tuple[str, ...] | None:
        """Devuelve las herramientas permitidas; None si el agente no existe."""
        return self.permisos.get(agente_id)


def autorizar_por_consola(agente: str, nombre: str) -> Autorizacion:
    """Crea un autorizador de consola con contexto de agente y herramienta.

    Uso: ``entorno.ejecutar(ag, tool, args, autorizar=autorizar_por_consola(ag, tool))``
    """

    def autorizar(previa: str) -> bool:
        print(f"[{agente}] propone '{nombre}':")
        for linea in previa.splitlines():
            print(f"  {linea}")
        return input("¿Autorizas? [s/N]: ").strip().lower() in ("s", "si", "sí", "y")

    return autorizar


class Entorno:
    """Media toda ejecución de herramientas: permisos, seguridad, confirmación y auditoría."""

    def __init__(
        self,
        equipo: Equipo,
        raiz: str | Path | None = None,
        auditoria: str | Path | None = LOG,
    ) -> None:
        self.equipo = equipo
        self.raiz = Path(raiz).resolve() if raiz is not None else ESPACIO
        self.auditoria = Path(auditoria) if auditoria is not None else None

    def ejecutar(
        self,
        agente_id: str,
        nombre: str,
        argumentos: dict | None = None,
        autorizar: Autorizacion | None = None,
    ) -> ResultadoAgente:
        """Ejecuta una herramienta en nombre de un agente. Nunca lanza por fallos."""
        argumentos = dict(argumentos or {})
        resultado = self._evaluar(agente_id, nombre, argumentos, autorizar)
        self._auditar(agente_id, nombre, argumentos, resultado.estado)
        return resultado

    def _evaluar(
        self,
        agente_id: str,
        nombre: str,
        argumentos: dict,
        autorizar: Autorizacion | None,
    ) -> ResultadoAgente:
        """Flujo: permisos → previsualización → autorización → ejecución."""
        herramienta = obtener(nombre)
        if herramienta is None:
            return ResultadoAgente.fallido(f"Herramienta desconocida: '{nombre}'.")

        permitidas = self.equipo.herramientas_de(agente_id)
        if permitidas is None:
            return ResultadoAgente.fallido(f"Agente desconocido: '{agente_id}'.")

        if nombre not in permitidas:
            return ResultadoAgente.denegado(
                f"El agente '{agente_id}' no tiene permiso para usar '{nombre}'."
            )

        try:
            if not herramienta.requiere_confirmacion:
                # Acciones seguras (lecturas): se ejecutan solas, sin preguntar.
                salida = herramienta.funcion(raiz=self.raiz, confirmar=False, **argumentos)
                return ResultadoAgente.ok(salida)

            # Paso 1: previsualizar SIEMPRE con confirmar=False (regla de oro).
            previa = herramienta.funcion(raiz=self.raiz, confirmar=False, **argumentos)

            # Paso 2: el humano decide. Sin autorizador → se niega (seguro por defecto).
            if autorizar is None or not autorizar(previa):
                return ResultadoAgente.rechazado(
                    previa, f"Acción '{nombre}' rechazada: el humano no autorizó."
                )

            # Paso 3: el proceso real corre con confirmar=True.
            salida = herramienta.funcion(raiz=self.raiz, confirmar=True, **argumentos)
            return ResultadoAgente.ok(salida)

        except ErrorRutaIlegal as exc:
            return ResultadoAgente.fallido(str(exc))
        except Exception as exc:  # el contrato captura todo
            return ResultadoAgente.fallido(f"{type(exc).__name__}: {exc}")

    def _auditar(self, agente: str, nombre: str, argumentos: dict, estado: Estado) -> None:
        """Traza cada ejecución en JSONL. La auditoría nunca tumba la ejecución."""
        if self.auditoria is None:
            return
        try:
            self.auditoria.parent.mkdir(parents=True, exist_ok=True)
            with self.auditoria.open("a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "t": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "agente": agente,
                            "herramienta": nombre,
                            "args": {k: str(v)[:80] for k, v in argumentos.items()},
                            "estado": estado.value,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except OSError:
            pass
