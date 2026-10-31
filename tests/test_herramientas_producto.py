"""Pruebas de las herramientas de producto (Fase 3).

Usan carpetas temporales y mockean ``send2trash`` para no borrar archivos
reales ni depender de la papelera del sistema.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mas.herramientas import (
    borrar_archivo,
    buscar_duplicados,
    crear_carpeta,
    listar_carpeta,
    mover_archivo,
    organizar_carpeta,
    escribir_archivo,
    leer_archivo,
)
from mas.tools import obtener


class TestListarCarpeta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "a.txt").write_text("hola", encoding="utf-8")
        (self.raiz / "b.txt").write_text("mundo", encoding="utf-8")
        (self.raiz / "sub").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_lista_archivos_con_tamano_y_fecha(self):
        r = listar_carpeta(".", raiz=self.raiz)
        self.assertIn("a.txt", r)
        self.assertIn("b.txt", r)
        self.assertIn("sub", r)  # las carpetas se marcan con '/' al inicio
        self.assertIn("bytes", r)

    def test_limite_de_resultados(self):
        for i in range(150):
            (self.raiz / f"f{i:03d}.txt").write_text("x", encoding="utf-8")
        r = listar_carpeta(".", raiz=self.raiz, limite=10)
        self.assertIn("mostrando las primeras 10", r)


class TestCrearCarpeta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_previsualiza_sin_crear(self):
        r = crear_carpeta("nueva/sub", raiz=self.raiz)
        self.assertIn("PREVISUALIZACIÓN", r)
        self.assertFalse((self.raiz / "nueva").exists())

    def test_crea_al_confirmar(self):
        r = crear_carpeta("nueva/sub", raiz=self.raiz, confirmar=True)
        self.assertTrue((self.raiz / "nueva" / "sub").is_dir())
        self.assertIn("creada", r)


class TestMoverArchivo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "origen.txt").write_text("contenido", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_previsualiza_sin_mover(self):
        r = mover_archivo("origen.txt", "destino.txt", raiz=self.raiz)
        self.assertIn("PREVISUALIZACIÓN", r)
        self.assertTrue((self.raiz / "origen.txt").exists())
        self.assertFalse((self.raiz / "destino.txt").exists())

    def test_mueve_al_confirmar(self):
        r = mover_archivo("origen.txt", "sub/destino.txt", raiz=self.raiz, confirmar=True)
        self.assertFalse((self.raiz / "origen.txt").exists())
        self.assertTrue((self.raiz / "sub" / "destino.txt").is_file())
        self.assertEqual((self.raiz / "sub" / "destino.txt").read_text(encoding="utf-8"), "contenido")

    def test_no_sobrescribe_sin_aviso(self):
        (self.raiz / "destino.txt").write_text("otro", encoding="utf-8")
        # mover_archivo lanza FileExistsError (el Entorno lo convierte a error)
        with self.assertRaises(FileExistsError):
            mover_archivo("origen.txt", "destino.txt", raiz=self.raiz, confirmar=True)


class TestBorrarArchivo(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "a.txt").write_text("a", encoding="utf-8")
        (self.raiz / "b.txt").write_text("b", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_previsualiza_sin_borrar(self):
        r = borrar_archivo("a.txt", raiz=self.raiz)
        self.assertIn("PREVISUALIZACIÓN", r)
        self.assertTrue((self.raiz / "a.txt").exists())

    @patch("mas.herramientas.send2trash.send2trash")
    def test_envia_a_la_papelera_al_confirmar(self, mock_trash):
        r = borrar_archivo("a.txt", raiz=self.raiz, confirmar=True)
        mock_trash.assert_called_once()
        # send2trash está mockeado, por eso el archivo sigue existiendo;
        # lo importante es que se llamó a send2trash con la ruta correcta.
        mock_trash.assert_called_with(str(self.raiz / "a.txt"))
        self.assertIn("papelera", r)

    @patch("mas.herramientas.send2trash.send2trash")
    def test_borrado_permanente(self, mock_trash):
        borrar_archivo("a.txt", raiz=self.raiz, confirmar=True, permanente=True)
        mock_trash.assert_not_called()
        self.assertFalse((self.raiz / "a.txt").exists())

    def test_no_borra_la_raiz(self):
        with self.assertRaises(__import__("mas.herramientas", fromlist=["ErrorRutaIlegal"]).ErrorRutaIlegal):
            borrar_archivo(".", raiz=self.raiz, confirmar=True)


class TestBuscarDuplicados(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "a.txt").write_text("contenido igual", encoding="utf-8")
        (self.raiz / "b.txt").write_text("contenido igual", encoding="utf-8")
        (self.raiz / "c.txt").write_text("contenido distinto", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_detecta_duplicados(self):
        r = buscar_duplicados(".", raiz=self.raiz)
        self.assertIn("a.txt", r)
        self.assertIn("b.txt", r)
        self.assertNotIn("c.txt", r)


class TestOrganizarCarpeta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.raiz = Path(self.tmp.name)
        (self.raiz / "foto.jpg").write_text("x", encoding="utf-8")
        (self.raiz / "doc.pdf").write_text("y", encoding="utf-8")
        (self.raiz / "nota.txt").write_text("z", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_propone_plan_sin_ejecutar(self):
        r = organizar_carpeta(".", raiz=self.raiz)
        self.assertIn("PREVISUALIZACIÓN" if "PREVISUALIZACIÓN" in r else "Plan de organización", r)
        self.assertIn("jpg", r)
        self.assertIn("pdf", r)
        self.assertIn("txt", r)
        # No se movió nada
        self.assertTrue((self.raiz / "foto.jpg").exists())

    def test_ejecuta_plan_al_confirmar(self):
        r = organizar_carpeta(".", raiz=self.raiz, confirmar=True)
        self.assertIn("completada", r)
        self.assertTrue((self.raiz / "jpg" / "foto.jpg").exists())
        self.assertTrue((self.raiz / "pdf" / "doc.pdf").exists())
        self.assertTrue((self.raiz / "txt" / "nota.txt").exists())


if __name__ == "__main__":
    unittest.main()
