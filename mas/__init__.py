"""MAS (Multi-Agent System): orquestador de agentes pequeños y modulares."""
from .agent import Agente
from .entorno import Entorno, Equipo, autorizar_por_consola
from .orchestrator import Informe, Orquestador, PasoEjecutado
from .providers import Proveedor
from .providers.fake import ProveedorFalso
from .result import Estado, ResultadoAgente
from .teams.loader import cargar_equipo

__all__ = [
    "Agente",
    "Orquestador",
    "Informe",
    "PasoEjecutado",
    "Estado",
    "ResultadoAgente",
    "Entorno",
    "Equipo",
    "autorizar_por_consola",
    "Proveedor",
    "ProveedorFalso",
    "cargar_equipo",
]
__version__ = "0.3.0"
