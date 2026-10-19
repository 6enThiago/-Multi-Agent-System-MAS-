import json

from mas.entorno import Entorno, autorizar_por_consola
from mas.teams.loader import cargar_equipo

equipo = cargar_equipo("equipos/laboral.yaml")
print(f"Equipo cargado: {equipo.nombre} -> {list(equipo.agentes)}")

entorno = Entorno(equipo) 


def caso(agente: str, herramienta: str, **args) -> None:
    r = entorno.ejecutar(
        agente, herramienta, args, autorizar=autorizar_por_consola(agente, herramienta)
    )
    print(f"{agente}/{herramienta}: {json.dumps(r.a_dict(), ensure_ascii=False)}")


caso("programador", "escribir_archivo", ruta="demo/hola.py", contenido="print('hola')")

caso("analista", "escribir_archivo", ruta="demo/x.txt", contenido="no debería")

caso("analista", "leer_archivo", ruta="demo/hola.py")

caso("analista", "leer_archivo", ruta="../../etc/passwd")
