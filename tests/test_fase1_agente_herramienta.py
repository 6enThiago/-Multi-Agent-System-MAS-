"""Pruebas de integración de la Fase 1: agente ↔ herramientas ↔ Entorno.

Criterio de aceptación:
  Un test con ProveedorFalso guionizado que pida escribir_archivo,
  pase por Entorno, y termine con una respuesta de texto; sin red.
"""
import tempfile
import unittest
from pathlib import Path

from mas.agent import Agente
from mas.entorno import Entorno, autorizar_por_consola
from mas.providers import LlamadaHerramienta, RespuestaModelo
from mas.providers.fake import ProveedorFalso
from mas.result import Estado
from mas.teams.loader import cargar_equipo
from mas.tools import esquema_de

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_LABORAL = RAIZ_PROYECTO / "equipos" / "laboral.yaml"


class TestAgenteUsaHerramienta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        self.equipo = cargar_equipo(RUTA_LABORAL)
        self.entorno = Entorno(
            self.equipo, raiz=self.raiz, auditoria=self.raiz / "audit.jsonl"
        )
        # El programador tiene permiso para escribir_archivo.
        self.herramientas_permitidas = self.equipo.herramientas_de("programador")

    def tearDown(self):
        self.tmp.cleanup()

    def test_pide_escribir_archivo_pasa_por_entorno_y_responde_texto(self):
        """El modelo pide escribir_archivo, el Entorno lo ejecuta, y el modelo da texto final."""
        proveedor = ProveedorFalso(
            guion=[
                # Primera respuesta: el modelo pide escribir el archivo.
                RespuestaModelo(
                    texto="",
                    llamada=LlamadaHerramienta(
                        nombre="escribir_archivo",
                        argumentos={"ruta": "notas/salida.md", "contenido": "hola mundo"},
                    ),
                ),
                # Segunda respuesta: texto final tras ver el resultado de la herramienta.
                RespuestaModelo(texto="He escrito el archivo correctamente."),
            ]
        )
        autorizador = lambda previa: True  # siempre autoriza

        agente = Agente(
            id="programador",
            rol="Programador",
            prompt_sistema="Eres un programador.",
            proveedor=proveedor,
            entorno=self.entorno,
            autorizar=autorizador,
            herramientas_permitidas=tuple(self.herramientas_permitidas),
        )

        resultado = agente.ejecutar("escribe un archivo de prueba")

        self.assertEqual(resultado.estado, Estado.OK)
        self.assertIn("He escrito el archivo correctamente", resultado.resultado)

        # El archivo se escribió de verdad en disco a través del Entorno.
        destino = self.raiz / "notas" / "salida.md"
        self.assertTrue(destino.is_file())
        self.assertEqual(destino.read_text(encoding="utf-8"), "hola mundo")

    def test_si_el_modelo_no_pide_herramienta_devuelve_texto_directo(self):
        """Si el modelo responde texto sin herramienta, el agente devuelve ese texto."""
        proveedor = ProveedorFalso(guion=["respuesta directa"])
        agente = Agente(
            id="programador",
            rol="Programador",
            prompt_sistema="Eres un programador.",
            proveedor=proveedor,
            entorno=self.entorno,
            herramientas_permitidas=tuple(self.herramientas_permitidas),
        )

        resultado = agente.ejecutar("di hola")

        self.assertEqual(resultado.estado, Estado.OK)
        self.assertEqual(resultado.resultado, "respuesta directa")

    def test_rechazo_vuelve_al_modelo_como_informacion(self):
        """Un RECHAZADO del humano vuelve al modelo para que lo explique o proponga otra cosa."""
        proveedor = ProveedorFalso(
            guion=[
                RespuestaModelo(
                    texto="",
                    llamada=LlamadaHerramienta(
                        nombre="escribir_archivo",
                        argumentos={"ruta": "notas/x.md", "contenido": "x"},
                    ),
                ),
                # Tras ver el rechazo, el modelo da una explicación en texto.
                RespuestaModelo(texto="El usuario no autorizó escribir ese archivo."),
            ]
        )
        autorizador = lambda previa: False  # siempre rechaza

        agente = Agente(
            id="programador",
            rol="Programador",
            prompt_sistema="Eres un programador.",
            proveedor=proveedor,
            entorno=self.entorno,
            autorizar=autorizador,
            herramientas_permitidas=tuple(self.herramientas_permitidas),
        )

        resultado = agente.ejecutar("escribe un archivo")

        self.assertEqual(resultado.estado, Estado.OK)
        self.assertIn("no autorizó", resultado.resultado)
        # El modelo debió hablar al menos dos veces: pidió la herramienta y,
        # tras ver el rechazo, dio una explicación en texto.
        self.assertGreaterEqual(len(proveedor.llamadas), 2)


class TestEsquemaHerramienta(unittest.TestCase):
    def test_esquema_de_leer_archivo(self):
        import mas.herramientas  # noqa: F401  (asegura el registro)

        esquema = esquema_de("leer_archivo")
        self.assertIsNotNone(esquema)
        self.assertEqual(esquema["nombre"], "leer_archivo")
        self.assertFalse(esquema["requiere_confirmacion"])
        self.assertIn("ruta", esquema["parametros"])
        self.assertTrue(esquema["parametros"]["ruta"]["obligatorio"])

    def test_esquema_de_escribir_archivo(self):
        import mas.herramientas  # noqa: F401  (asegura el registro)

        esquema = esquema_de("escribir_archivo")
        self.assertIsNotNone(esquema)
        self.assertTrue(esquema["requiere_confirmacion"])
        self.assertIn("ruta", esquema["parametros"])
        self.assertIn("contenido", esquema["parametros"])

    def test_esquema_desconocido_devuelve_none(self):
        from mas.tools import esquema_de

        self.assertIsNone(esquema_de("no_existe"))


if __name__ == "__main__":
    unittest.main()
