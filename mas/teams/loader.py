"""Carga de equipos desde YAML (esquema único tras la convergencia).

Esquema (``equipos/*.yaml``)::

    equipo: nombre
    descripcion: ...
    orquestador: id-del-agente-orquestador
    agentes:
      - nombre: ...
        rol: ...
        herramientas: [...]

Valida: claves obligatorias, agentes duplicados, herramientas
inexistentes en el registro y que el orquestador exista entre los agentes.

Convención del proyecto: una herramienta nueva se escribe primero con el
decorador y después se añade su nombre en el YAML del agente que la
necesite. Sin nombre en el YAML, la herramienta queda denegada.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from .. import herramientas as _herramientas  # noqa: F401  (asegura el registro de las built-in)
from ..entorno import Equipo
from ..tools import REGISTRO


def cargar_equipo(ruta: str | Path) -> Equipo:
    """Lee un YAML de equipo, lo valida y devuelve sus permisos por agente."""
    ruta = Path(ruta)
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))

    if not isinstance(datos, dict):
        raise ValueError(f"Formato de equipo inválido: {ruta}")

    for clave in ("equipo", "orquestador", "agentes"):
        if clave not in datos:
            raise ValueError(f"Falta la clave '{clave}' en {ruta}")

    permisos: dict[str, tuple[str, ...]] = {}
    for agente in datos["agentes"]:
        if "id" in agente and "nombre" not in agente:
            raise ValueError(f"Esquema antiguo en {ruta}: usa 'nombre' en lugar de 'id'")

        nombre = agente.get("nombre")
        if not nombre:
            raise ValueError(f"Agente sin 'nombre' en {ruta}")
        if nombre in permisos:
            raise ValueError(f"Agente duplicado: '{nombre}' en {ruta}")

        for herramienta in agente.get("herramientas", []):
            if herramienta not in REGISTRO:
                raise ValueError(f"'{nombre}' usa herramienta inexistente: '{herramienta}'")

        permisos[nombre] = tuple(agente.get("herramientas", []))

    if datos["orquestador"] not in permisos:
        raise ValueError(f"El orquestador '{datos['orquestador']}' no está en agentes")

    return Equipo(
        nombre=datos["equipo"],
        descripcion=str(datos.get("descripcion", "")),
        orquestador=datos["orquestador"],
        permisos=permisos,
    )
