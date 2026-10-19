"""Interfaz CLI del MAS (sistema unificado tras la convergencia).

- ``mas run``: cadena de agentes con el equipo de demo (proveedor falso).
- ``mas tool``: ejecuta una herramienta con permisos YAML, previsualización,
  confirmación por consola y auditoría (humano en el control).
"""
from __future__ import annotations

import argparse
import json
import sys

from .agent import Agente
from .entorno import Entorno, autorizar_por_consola
from .orchestrator import Orquestador
from .providers.fake import ProveedorFalso
from .result import Estado
from .teams.loader import cargar_equipo

EQUIPO_POR_DEFECTO = "equipos/laboral.yaml"


def equipo_demo() -> list[Agente]:
    """Equipo de demostración: investigador -> redactor -> corrector."""
    proveedor = ProveedorFalso()
    return [
        Agente("researcher", "Investigador", "Recopila y resume la evidencia en puntos clave.", proveedor),
        Agente("writer", "Redactor", "Convierte la investigación en un informe estructurado.", proveedor),
        Agente("reviewer", "Corrector", "Pule el texto y valida que cumple el objetivo.", proveedor),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mas", description="Orquestador de agentes de IA (MAS)")
    sub = parser.add_subparsers(dest="orden", required=True)

    run = sub.add_parser("run", help="Ejecuta el equipo por defecto con una tarea")
    run.add_argument("--task", required=True, help="Tarea u objetivo a resolver")

    tool = sub.add_parser("tool", help="Ejecuta una herramienta como un agente (humano en el control)")
    tool.add_argument("--agent", required=True, help="id del agente (debe existir en el YAML del equipo)")
    tool.add_argument("--tool", required=True, help="nombre de la herramienta registrada")
    tool.add_argument("--arg", action="append", default=[], metavar="clave=valor", help="argumento de la herramienta (repetible)")
    tool.add_argument("--team", default=EQUIPO_POR_DEFECTO, help="ruta al YAML del equipo")
    tool.add_argument("--raiz", default=None, help="área de trabajo (default: espacio_trabajo/)")

    args = parser.parse_args(argv)

    if args.orden == "tool":
        return _cmd_tool(args)

    informe = Orquestador().ejecutar(args.task, equipo_demo())
    print(json.dumps(informe.a_dict(), ensure_ascii=False, indent=2))
    return 0 if informe.estado is Estado.OK else 1


def _cmd_tool(args: argparse.Namespace) -> int:
    """Ejecuta una herramienta respetando permisos YAML y confirmación humana."""
    argumentos: dict[str, str] = {}
    for item in args.arg:
        clave, _, valor = item.partition("=")
        argumentos[clave] = valor

    equipo = cargar_equipo(args.team)
    entorno = Entorno(equipo, raiz=args.raiz)  # raiz None → espacio_trabajo/
    autorizador = autorizar_por_consola(args.agent, args.tool)
    resultado = entorno.ejecutar(args.agent, args.tool, argumentos, autorizador)
    print(json.dumps(resultado.a_dict(), ensure_ascii=False, indent=2))
    return 0 if resultado.estado is Estado.OK else 1


if __name__ == "__main__":
    sys.exit(main())
