"""MAS (Multi-Agent System): orquestador de agentes pequeños y modulares."""
from .agent import Agente
from .entorno import Entorno, Equipo, autorizar_por_consola
from .orchestrator import Informe, Orquestador, PasoEjecutado
from .result import Estado, ResultadoAgente

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
]
__version__ = "0.3.0"
