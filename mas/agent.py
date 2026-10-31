"""Agente: una sola responsabilidad.

Principio: "Un agente, una responsabilidad".
Un agente hace una cosa bien y nunca habla con otro agente directamente:
toda coordinación la hace el orquestador.

El agente ejecuta un bucle de herramientas:

    1. pregunta al modelo (proveedor.completar)
    2. si el modelo pide una herramienta, la ejecuta a través del Entorno
    3. el resultado vuelve al modelo como parte del historial
    4. se repite hasta que el modelo devuelva texto final o se agotan las
       iteraciones (por defecto 6, para evitar ciclos infinitos)

Toda ejecución devuelve el contrato estandarizado (ResultadoAgente) y
nunca lanza excepciones.
"""
from __future__ import annotations

from dataclasses import dataclass

from .entorno import Autorizacion, Entorno
from .providers import Proveedor, RespuestaModelo
from .result import Estado, ResultadoAgente
from .tools import listar_esquemas, obtener

MAX_ITER_POR_DEFECTO = 6


def _formatear_esquemas(esquemas: list[dict]) -> str:
    """Convierte los esquemas de herramientas en texto legible para el modelo."""
    lineas = []
    for esquema in esquemas:
        lineas.append(f"- {esquema['nombre']}: {esquema['descripcion']}")
        lineas.append(f"  confirma: {esquema['requiere_confirmacion']}")
        if esquema["parametros"]:
            lineas.append("  parámetros:")
            for nombre_param, info in esquema["parametros"].items():
                obligatorio = "obligatorio" if info["obligatorio"] else "opcional"
                lineas.append(
                    f"    - {nombre_param} ({info['tipo']}, {obligatorio}): {info['descripcion']}"
                )
        else:
            lineas.append("  parámetros: (ninguno)")
    return "\n".join(lineas)


@dataclass
class Agente:
    """Unidad autónoma con un rol único, un proveedor de modelos y acceso al Entorno."""

    id: str
    rol: str
    prompt_sistema: str
    proveedor: Proveedor

    # --- dependencias inyectadas (no importadas globalmente) ----------------
    entorno: Entorno | None = None
    autorizar: Autorizacion | None = None
    herramientas_permitidas: tuple[str, ...] = ()
    max_iter: int = MAX_ITER_POR_DEFECTO

    def ejecutar(self, tarea: str, contexto: str = "") -> ResultadoAgente:
        """Ejecuta su única responsabilidad con bucle de herramientas.

        Recibe solo contexto mínimo (nunca la conversación completa)
        y **nunca lanza excepciones**: todo error vuelve dentro del
        contrato estandarizado.
        """
        try:
            # Construir el historial inicial con contexto mínimo.
            historial: list[str] = []
            if contexto:
                historial.append(f"Contexto previo:\n{contexto}")
            historial.append(f"Tarea: {tarea}")

            # Describir las herramientas disponibles al modelo.
            if self.herramientas_permitidas:
                esquemas = listar_esquemas(list(self.herramientas_permitidas))
                historial.append("\nHerramientas disponibles:\n" + _formatear_esquemas(esquemas))

            for _ in range(self.max_iter):
                entrada = "\n\n".join(historial)
                respuesta = self.proveedor.completar(entrada, sistema=self.prompt_sistema)

                # Caso 1: el modelo da una respuesta final (sin herramienta).
                if respuesta.llamada is None:
                    return ResultadoAgente.ok(respuesta.texto)

                # Caso 2: el modelo pide ejecutar una herramienta.
                llamada = respuesta.llamada
                nombre = llamada.nombre
                argumentos = dict(llamada.argumentos or {})

                if self.entorno is None:
                    resultado = ResultadoAgente.fallido(
                        "El agente no tiene un Entorno asignado para ejecutar herramientas."
                    )
                elif nombre not in self.herramientas_permitidas:
                    resultado = ResultadoAgente.denegado(
                        f"El agente '{self.id}' no tiene permiso para usar '{nombre}'."
                    )
                else:
                    herramienta = obtener(nombre)
                    if herramienta is None:
                        resultado = ResultadoAgente.fallido(
                            f"Herramienta desconocida: '{nombre}'."
                        )
                    else:
                        resultado = self.entorno.ejecutar(
                            self.id, nombre, argumentos, self.autorizar
                        )

                # El resultado (incluido RECHAZADO/DENEGADO) vuelve al modelo
                # como información para que pueda explicar o proponer otra cosa.
                historial.append(
                    f"\nResultado de '{nombre}': {resultado.resultado}"
                    + (f" ({'; '.join(resultado.errores)})" if resultado.errores else "")
                )

            # Se agotaron las iteraciones sin respuesta final.
            return ResultadoAgente.fallido(
                f"Demasiadas iteraciones ({self.max_iter}) sin respuesta final del modelo."
            )

        except Exception as exc:  # el contrato captura todo, sin excepciones
            return ResultadoAgente.fallido(f"{type(exc).__name__}: {exc}")
