"""Pruebas del contrato de salida estandarizado (principio 4)."""
import unittest

from mas.result import Estado, ResultadoAgente


class TestResultadoAgente(unittest.TestCase):
    def test_ok_sigue_el_contrato(self):
        r = ResultadoAgente.ok("  hola  ")
        self.assertEqual(r.estado, Estado.OK)
        self.assertEqual(r.resultado, "  hola  ")  # el texto se devuelve tal cual, sin recortar
        self.assertEqual(r.errores, ())
        self.assertTrue(r.es_ok)

    def test_fallido_guarda_los_errores(self):
        r = ResultadoAgente.fallido("e1", "e2")
        self.assertEqual(r.estado, Estado.ERROR)
        self.assertFalse(r.es_ok)
        self.assertEqual(r.resultado, "")
        self.assertEqual(r.errores, ("e1", "e2"))

    def test_a_dict_tiene_exactamente_las_tres_claves(self):
        self.assertEqual(set(ResultadoAgente.ok("x").a_dict()), {"estado", "resultado", "errores"})
        self.assertEqual(set(ResultadoAgente.fallido("e").a_dict()), {"estado", "resultado", "errores"})

    def test_es_inmutable(self):
        r = ResultadoAgente.ok("x")
        with self.assertRaises(AttributeError):
            r.resultado = "otro"


if __name__ == "__main__":
    unittest.main()
