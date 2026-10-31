"""Pruebas del orquestador (cadena, contexto mínimo, parada ante fallo, reintentos)."""
import unittest

from mas.agent import Agente
from mas.orchestrator import Orquestador
from mas.providers import RespuestaModelo
from mas.providers.fake import ProveedorFalso
from mas.result import Estado


class ProveedorContador:
    """Cuenta las llamadas y falla las N primeras (simula fallos intermitentes)."""

    def __init__(self, fallos: int = 0) -> None:
        self.fallos = fallos
        self.llamadas = 0

    def completar(self, entrada: str, *, sistema: str) -> RespuestaModelo:
        self.llamadas += 1
        if self.llamadas <= self.fallos:
            raise RuntimeError("fallo simulado")
        return RespuestaModelo(texto=f"salida-de-{sistema}")


class TestOrquestador(unittest.TestCase):
    def test_cadena_feliz_y_contexto_minimo(self):
        p1 = ProveedorFalso(guion=["investigación"])
        p2 = ProveedorFalso(guion=["informe"])
        equipo = [
            Agente("researcher", "Investigador", "inv", p1),
            Agente("writer", "Redactor", "esc", p2),
        ]
        informe = Orquestador().ejecutar("escribe", equipo)

        self.assertEqual(informe.estado, Estado.OK)
        self.assertEqual(informe.resultado, "informe")  # manda el último paso
        self.assertEqual(len(informe.pasos), 2)
        self.assertTrue(all(p.intentos_usados == 1 for p in informe.pasos))
        # Contexto mínimo: el 2º agente solo ve la salida del 1º, no más.
        _sistema, entrada_del_2 = p2.llamadas[0]
        self.assertIn("investigación", entrada_del_2)
        self.assertNotIn("informe", entrada_del_2)

    def test_fallo_detiene_la_cadena(self):
        p1 = ProveedorFalso(excepcion=RuntimeError("caído"))
        p2 = ProveedorFalso(guion=["no debería usarse"])
        equipo = [Agente("a", "A", "s1", p1), Agente("b", "B", "s2", p2)]

        informe = Orquestador().ejecutar("tarea", equipo)

        self.assertEqual(informe.estado, Estado.ERROR)
        self.assertEqual(informe.resultado, "")
        self.assertEqual(len(informe.pasos), 1)  # el 2º nunca corrió
        self.assertEqual(p2.llamadas, [])
        self.assertIn("Falló el agente 'a'", informe.errores[0])

    def test_reintenta_una_vez_y_despues_pasa(self):
        proveedor = ProveedorContador(fallos=1)
        equipo = [Agente("a", "A", "s", proveedor)]

        informe = Orquestador(reintentos_maximos=1).ejecutar("t", equipo)

        self.assertEqual(informe.estado, Estado.OK)
        self.assertEqual(informe.pasos[0].intentos_usados, 2)
        self.assertEqual(proveedor.llamadas, 2)

    def test_reintentos_agotados_reportan_error(self):
        proveedor = ProveedorContador(fallos=99)
        equipo = [Agente("a", "A", "s", proveedor)]

        informe = Orquestador(reintentos_maximos=1).ejecutar("t", equipo)

        self.assertEqual(informe.estado, Estado.ERROR)
        self.assertEqual(informe.pasos[0].intentos_usados, 2)  # 1 intento + 1 reintento

    def test_equipo_vacio_es_error_estandarizado(self):
        informe = Orquestador().ejecutar("t", [])
        self.assertEqual(informe.estado, Estado.ERROR)
        self.assertIn("vacío", informe.errores[0])

    def test_informe_sigue_el_contrato(self):
        informe = Orquestador().ejecutar("t", [Agente("a", "A", "s", ProveedorFalso())])
        d = informe.a_dict()
        self.assertEqual(set(d), {"estado", "resultado", "errores", "pasos"})
        self.assertEqual(
            set(d["pasos"][0]),
            {"agente", "intentos", "estado", "resultado", "errores"},
        )

    def test_reintentos_negativos_se_rechazan(self):
        with self.assertRaises(ValueError):
            Orquestador(reintentos_maximos=-1)


if __name__ == "__main__":
    unittest.main()
