"""Pruebas de la matriz de autorización y del gestor de equipos (sistema unificado).

Casos de la tabla acordada:
- Programador escribe, se autoriza        → ok
- Programador escribe, se rechaza         → rechazado
- Analista intenta escribir (sin permiso) → denegado
- Analista lee un archivo                 → ok, sin preguntar
- Leer ../../etc/passwd                   → error (bloqueado)
"""
import json
import tempfile
import unittest
from pathlib import Path

from mas.entorno import Entorno
from mas.result import Estado
from mas.teams.loader import cargar_equipo

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
RUTA_LABORAL = RAIZ_PROYECTO / "equipos" / "laboral.yaml"
RUTA_DEMO = RAIZ_PROYECTO / "equipos" / "demo.yaml"


class TestMatrizDeAutorizacion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        self.entorno = Entorno(
            cargar_equipo(RUTA_LABORAL), raiz=self.raiz, auditoria=self.raiz / "audit.jsonl"
        )
        self.escritura = {"ruta": "notas/salida.md", "contenido": "hola"}

    def tearDown(self):
        self.tmp.cleanup()

    # --- programador escribe ---

    def test_programador_escribe_y_se_autoriza_ok(self):
        r = self.entorno.ejecutar(
            "programador", "escribir_archivo", self.escritura, autorizar=lambda previa: True
        )
        self.assertEqual(r.estado, Estado.OK)
        destino = self.raiz / "notas" / "salida.md"
        self.assertTrue(destino.is_file())  # se escribió de verdad
        self.assertEqual(destino.read_text(encoding="utf-8"), "hola")

    def test_programador_escribe_y_se_rechaza_rechazado(self):
        r = self.entorno.ejecutar(
            "programador", "escribir_archivo", self.escritura, autorizar=lambda previa: False
        )
        self.assertEqual(r.estado, Estado.RECHAZADO)
        self.assertIn("PREVISUALIZACIÓN", r.resultado)  # se ve qué se rechazó
        self.assertFalse((self.raiz / "notas" / "salida.md").exists())  # nada tocado

    def test_sin_autorizador_se_rechaza_por_defecto(self):
        r = self.entorno.ejecutar("programador", "escribir_archivo", self.escritura)
        self.assertEqual(r.estado, Estado.RECHAZADO)
        self.assertFalse((self.raiz / "notas" / "salida.md").exists())

    def test_se_previsualiza_antes_de_preguntar(self):
        vistas = []
        self.entorno.ejecutar(
            "programador",
            "escribir_archivo",
            self.escritura,
            autorizar=lambda p: vistas.append(p) or False,
        )
        self.assertEqual(len(vistas), 1)
        self.assertIn("PREVISUALIZACIÓN", vistas[0])

    # --- analista sin permisos ---

    def test_analista_escribe_sin_permiso_denegado(self):
        preguntas = []
        r = self.entorno.ejecutar(
            "analista", "escribir_archivo", self.escritura, autorizar=lambda p: preguntas.append(p) or True
        )
        self.assertEqual(r.estado, Estado.DENEGADO)
        self.assertEqual(preguntas, [])  # ni siquiera se llegó a preguntar
        self.assertFalse((self.raiz / "notas" / "salida.md").exists())

    def test_analista_lee_ok_sin_preguntar(self):
        (self.raiz / "datos.txt").write_text("información útil", encoding="utf-8")
        preguntas = []
        r = self.entorno.ejecutar(
            "analista", "leer_archivo", {"ruta": "datos.txt"}, autorizar=lambda p: preguntas.append(p) or True
        )
        self.assertEqual(r.estado, Estado.OK)
        self.assertIn("información útil", r.resultado)
        self.assertEqual(preguntas, [])  # sin preguntar

    # --- seguridad de rutas ---

    def test_leer_ruta_ilegal_bloqueado(self):
        r = self.entorno.ejecutar("analista", "leer_archivo", {"ruta": "../../etc/passwd"})
        self.assertEqual(r.estado, Estado.ERROR)
        self.assertIn("bloqueada", r.errores[0])

    def test_escribir_ruta_ilegal_bloqueado_aunque_autorizen(self):
        r = self.entorno.ejecutar(
            "programador",
            "escribir_archivo",
            {"ruta": "../fuera.txt", "contenido": "x"},
            autorizar=lambda previa: True,
        )
        self.assertEqual(r.estado, Estado.ERROR)
        self.assertFalse((self.raiz.parent / "fuera.txt").exists())

    def test_ruta_absoluta_tambien_bloqueada(self):
        r = self.entorno.ejecutar("analista", "leer_archivo", {"ruta": "/etc/passwd"})
        self.assertEqual(r.estado, Estado.ERROR)

    # --- casos límite ---

    def test_agente_desconocido_es_error(self):
        r = self.entorno.ejecutar("pirata", "leer_archivo", {"ruta": "x"})
        self.assertEqual(r.estado, Estado.ERROR)
        self.assertIn("desconocido", r.errores[0])

    def test_herramienta_desconocida_es_error(self):
        r = self.entorno.ejecutar("programador", "borrar_todo", {})
        self.assertEqual(r.estado, Estado.ERROR)

    def test_archivo_inexistente_es_error(self):
        r = self.entorno.ejecutar("analista", "leer_archivo", {"ruta": "no-existe.txt"})
        self.assertEqual(r.estado, Estado.ERROR)
        self.assertIn("No existe", r.errores[0])

    # --- auditoría (heredada de core/) ---

    def test_auditoria_registra_cada_ejecucion(self):
        self.entorno.ejecutar(
            "programador", "escribir_archivo", self.escritura, autorizar=lambda previa: True
        )
        self.entorno.ejecutar("analista", "escribir_archivo", self.escritura)
        self.entorno.ejecutar("analista", "leer_archivo", {"ruta": "no-existe.txt"})

        lineas = (self.raiz / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lineas), 3)
        registradas = [json.loads(linea) for linea in lineas]
        self.assertEqual([e["estado"] for e in registradas], ["ok", "denegado", "error"])
        self.assertEqual([e["agente"] for e in registradas], ["programador", "analista", "analista"])
        self.assertEqual(registradas[0]["herramienta"], "escribir_archivo")
        self.assertIn("t", registradas[0])

    def test_sin_auditoria_no_escribe_nada(self):
        sin_log = Entorno(cargar_equipo(RUTA_DEMO), raiz=self.raiz, auditoria=None)
        sin_log.ejecutar("analista", "leer_archivo", {"ruta": "x"})
        self.assertFalse((self.raiz / "audit.jsonl").exists())


class TestCargaDeEquipos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _yaml(self, contenido: str) -> Path:
        ruta = self.dir / "equipo.yaml"
        ruta.write_text(contenido, encoding="utf-8")
        return ruta

    def test_carga_el_equipo_laboral(self):
        equipo = cargar_equipo(RUTA_LABORAL)
        self.assertEqual(equipo.nombre, "laboral")
        self.assertEqual(equipo.orquestador, "orquestador")
        self.assertEqual(equipo.herramientas_de("analista"), ("leer_archivo",))
        self.assertEqual(
            equipo.herramientas_de("programador"), ("leer_archivo", "escribir_archivo")
        )
        self.assertIsNone(equipo.herramientas_de("nadie"))  # agente inexistente
        self.assertIn("documentador", equipo.agentes)

    def test_carga_el_equipo_demo(self):
        equipo = cargar_equipo(RUTA_DEMO)
        self.assertEqual(equipo.nombre, "demo")
        self.assertEqual(equipo.orquestador, "orquestador")

    def test_falla_si_falta_una_clave_obligatoria(self):
        ruta = self._yaml("equipo: x\nagentes: []\n")
        with self.assertRaisesRegex(ValueError, "orquestador"):
            cargar_equipo(ruta)

    def test_falla_si_herramienta_inexistente(self):
        ruta = self._yaml(
            "equipo: x\norquestador: a\nagentes:\n"
            "  - nombre: a\n    herramientas: [borrar_todo]\n"
        )
        with self.assertRaisesRegex(ValueError, "inexistente"):
            cargar_equipo(ruta)

    def test_falla_si_orquestador_no_esta_en_agentes(self):
        ruta = self._yaml(
            "equipo: x\norquestador: fantasma\nagentes:\n"
            "  - nombre: a\n    herramientas: [leer_archivo]\n"
        )
        with self.assertRaisesRegex(ValueError, "no está en agentes"):
            cargar_equipo(ruta)

    def test_falla_si_agente_duplicado(self):
        ruta = self._yaml(
            "equipo: x\norquestador: a\nagentes:\n"
            "  - nombre: a\n    herramientas: []\n"
            "  - nombre: a\n    herramientas: []\n"
        )
        with self.assertRaisesRegex(ValueError, "duplicado"):
            cargar_equipo(ruta)

    def test_falla_si_esquema_antiguo_usa_id(self):
        ruta = self._yaml(
            "equipo: x\norquestador: a\nagentes:\n  - id: a\n    herramientas: []\n"
        )
        with self.assertRaisesRegex(ValueError, "antiguo"):
            cargar_equipo(ruta)


if __name__ == "__main__":
    unittest.main()
