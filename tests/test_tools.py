"""Pruebas del registro de herramientas y la regla de oro del decorador."""
import unittest

from mas.tools import REGISTRO, herramienta, obtener


class TestDecoradorHerramienta(unittest.TestCase):
    def test_herramienta_valida_se_registra(self):
        @herramienta("prueba_valida")
        def prueba_valida(texto: str, *, raiz=None, confirmar: bool = False) -> str:
            """De prueba."""
            return texto

        h = obtener("prueba_valida")
        self.assertIsNotNone(h)
        self.assertEqual(h.nombre, "prueba_valida")
        self.assertFalse(h.requiere_confirmacion)
        self.assertEqual(h.descripcion, "De prueba.")

    def test_sin_parametro_confirmar_no_se_registra(self):
        with self.assertRaises(TypeError):
            @herramienta("prueba_sin_confirmar")
            def mala(x: str) -> str:
                return x
        self.assertIsNone(obtener("prueba_sin_confirmar"))

    def test_confirmar_con_default_distinto_de_false_no_se_registra(self):
        with self.assertRaises(TypeError):
            @herramienta("prueba_default_verdadero")
            def mala2(x: str, *, confirmar: bool = True) -> str:
                return x
        self.assertIsNone(obtener("prueba_default_verdadero"))

    def test_nombre_duplicado_se_rechaza(self):
        @herramienta("prueba_duplicada", requiere_confirmacion=True)
        def f1(*, raiz=None, confirmar: bool = False) -> str:
            return "1"

        with self.assertRaises(ValueError):
            @herramienta("prueba_duplicada")
            def f2(*, raiz=None, confirmar: bool = False) -> str:
                return "2"

    def test_herramientas_de_ejemplo_estan_registradas(self):
        import mas.herramientas  # noqa: F401  (asegura el registro)

        leer = obtener("leer_archivo")
        escribir = obtener("escribir_archivo")
        self.assertIsNotNone(leer)
        self.assertIsNotNone(escribir)
        self.assertFalse(leer.requiere_confirmacion)  # lectura: sola, sin preguntar
        self.assertTrue(escribir.requiere_confirmacion)  # escritura: con confirmación

    def test_buscar_desconocida_da_none(self):
        self.assertIsNone(obtener("no_existe"))
        self.assertIn("leer_archivo", REGISTRO)


if __name__ == "__main__":
    unittest.main()
