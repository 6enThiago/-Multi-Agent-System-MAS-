"""Carga de equipos desde YAML (esquema único tras la convergencia).

Esquema (``equipos/*.yaml``)::

    equipo: nombre
    descripcion: ...
    orquestador: id-del-agente-orquestador
    agentes:
      - nombre: ...
        rol: ...
        prompt_sistema: ...        # opcional: instrucciones del agente
        proveedor: ...             # opcional: proveedor de IA del agente
        modelo: ...                # opcional: nombre del modelo
        herramientas: [...]

Valida: claves obligatorias, que ``agentes`` sea una lista de diccionarios,
que ``herramientas`` sea una lista (no texto), agentes duplicados,
herramientas inexistentes en el registro y que el orquestador exista
entre los agentes.

Los campos opcionales ``prompt_sistema``, ``proveedor`` y ``modelo`` se
aceptan por agente (sin validar su valor aquí); la aplicación decide
cómo usarlos al construir los ``Agente``.

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


def _validar_agente(agente: object, ruta: Path) -> dict:
    """Devuelve el agente como diccionario o lanza ValueError descriptivo."""
    if not isinstance(agente, dict):
        raise ValueError(
            f"Cada agente debe ser un mapeo (diccionario) en {ruta}; se recibió {type(agente).__name__}"
        )
    return agente


def _validar_herramientas(herramientas: object, nombre_agente: str, ruta: Path) -> list[str]:
    """Devuelve la lista de herramientas o lanza ValueError si no es una lista."""
    if not isinstance(herramientas, list):
        raise ValueError(
            f"'{nombre_agente}' en {ruta}: 'herramientas' debe ser una lista, "
            f"se recibió {type(herramientas).__name__}"
        )
    for herramienta in herramientas:
        if not isinstance(herramienta, str):
            raise ValueError(
                f"'{nombre_agente}' en {ruta}: cada elemento de 'herramientas' debe ser texto, "
                f"se recibió {type(herramienta).__name__}"
            )
        if herramienta not in REGISTRO:
            raise ValueError(f"'{nombre_agente}' usa herramienta inexistente: '{herramienta}'")
    return herramientas


def cargar_equipo(ruta: str | Path) -> Equipo:
    """Lee un YAML de equipo, lo valida y devuelve sus permisos por agente."""
    ruta = Path(ruta)
    datos = yaml.safe_load(ruta.read_text(encoding="utf-8"))

    if not isinstance(datos, dict):
        raise ValueError(f"Formato de equipo inválido: {ruta}")

    for clave in ("equipo", "orquestador", "agentes"):
        if clave not in datos:
            raise ValueError(f"Falta la clave '{clave}' en {ruta}")

    if not isinstance(datos["agentes"], list):
        raise ValueError(f"'agentes' en {ruta} debe ser una lista")

    permisos: dict[str, tuple[str, ...]] = {}
    for agente in datos["agentes"]:
        agente = _validar_agente(agente, ruta)

        if "id" in agente and "nombre" not in agente:
            raise ValueError(f"Esquema antiguo en {ruta}: usa 'nombre' en lugar de 'id'")

        nombre = agente.get("nombre")
        if not nombre:
            raise ValueError(f"Agente sin 'nombre' en {ruta}")
        if nombre in permisos:
            raise ValueError(f"Agente duplicado: '{nombre}' en {ruta}")

        herramientas_raw = agente.get("herramientas", [])
        herramientas_validadas = _validar_herramientas(herramientas_raw, nombre, ruta)

        # Los campos opcionales se aceptan sin validar valor; la app los usa al construir Agente.
        for campo_opcional in ("prompt_sistema", "proveedor", "modelo"):
            if campo_opcional in agente and not isinstance(agente[campo_opcional], str):
                raise ValueError(
                    f"'{nombre}' en {ruta}: '{campo_opcional}' debe ser texto si se indica"
                )

        permisos[nombre] = tuple(herramientas_validadas)

    if datos["orquestador"] not in permisos:
        raise ValueError(f"El orquestador '{datos['orquestador']}' no está en agentes")

    return Equipo(
        nombre=datos["equipo"],
        descripcion=str(datos.get("descripcion", "")),
        orquestador=datos["orquestador"],
        permisos=permisos,
    )
