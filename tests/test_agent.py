"""Pruebas del agente (una responsabilidad, contexto mínimo, nunca lanza)."""
import unittest

from mas.agent import Agente
from mas.providers.fake import ProveedorFalso
from mas.result import Estado


def agente_con(proveedor: ProveedorFalso) -> Agente:
    return Agente("probador", "Rol de prueba", "Eres un agente de pruebas.", proveedor)


class TestAgente(unittest.TestCase):
    def test_ejecuta_y_devuelve_el_contrato(self):
        proveedor = ProveedorFalso(guion=["listo"])
        r = agente_con(proveedor).ejecutar("tarea x")
        self.assertEqual(r.estado, Estado.OK)
        self.assertEqual(r.resultado, "listo")
        _sistema, entrada = proveedor.llamadas[0]
        self.assertIn("Tarea: tarea x", entrada)  # la tarea siempre viaja

    def test_sin_contexto_no_se_inyecta_nada(self):
        proveedor = ProveedorFalso()
        agente_con(proveedor).ejecutar("tarea")
        _sistema, entrada = proveedor.llamadas[0]
        self.assertNotIn("Contexto previo", entrada)

    def test_con_contexto_minimo_se_inyecta(self):
        proveedor = ProveedorFalso()
        agente_con(proveedor).ejecutar("tarea", contexto="dato clave")
        _sistema, entrada = proveedor.llamadas[0]
        self.assertIn("Contexto previo:\ndato clave", entrada)

    def test_error_del_proveedor_no_escapa(self):
        proveedor = ProveedorFalso(excepcion=RuntimeError("sin red"))
        r = agente_con(proveedor).ejecutar("tarea")
        self.assertEqual(r.estado, Estado.ERROR)
        self.assertIn("sin red", r.errores[0])

    def test_las_llamadas_llevan_el_prompt_sistema(self):
        proveedor = ProveedorFalso()
        agente_con(proveedor).ejecutar("tarea")
        sistema, _entrada = proveedor.llamadas[0]
        self.assertEqual(sistema, "Eres un agente de pruebas.")


if __name__ == "__main__":
    unittest.main()
