import unittest

from zelador.executor import Executor, ExecutorFalso, Resultado


class TestExecutorFalso(unittest.TestCase):
    def test_falso_casa_prefixo_mais_longo(self):
        ex = ExecutorFalso({
            ("systemctl",): Resultado(0, "a", ""),
            ("systemctl", "--user", "is-active"): Resultado(0, "active", ""),
        })
        r = ex.rodar(["systemctl", "--user", "is-active", "x"])
        self.assertEqual(r.saida, "active")
        self.assertEqual(ex.chamadas[-1], ["systemctl", "--user", "is-active", "x"])

    def test_falso_sem_casamento_127(self):
        r = ExecutorFalso({}).rodar(["nada"])
        self.assertEqual(r.codigo, 127)


class TestExecutorReal(unittest.TestCase):
    def test_executor_real_lista_de_args(self):
        self.assertEqual(Executor().rodar(["printf", "%s", "a b"]).saida, "a b")

    def test_executor_real_comando_inexistente(self):
        self.assertEqual(Executor().rodar(["comando-que-nao-existe-zelador"]).codigo, 127)


if __name__ == "__main__":
    unittest.main()
