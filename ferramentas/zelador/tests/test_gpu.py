import unittest
from pathlib import Path

from zelador import gpu
from zelador.executor import ExecutorFalso, Resultado

TABELA = (Path(__file__).parent / "fixtures/nvidia-smi.txt").read_text()


def ex_com(tabela):
    return ExecutorFalso({("nvidia-smi",): Resultado(0, tabela, "")})


class TestGpu(unittest.TestCase):
    def test_processos_le_tabela(self):
        ps = gpu.processos(ex_com(TABELA))
        self.assertIn({"pid": 26589, "nome": "eden", "mib": 746}, ps)
        self.assertIn({"pid": 6892, "nome": "steamwebhelper", "mib": 217}, ps)

    def test_jogo_rodando_detecta_eden(self):
        self.assertEqual(gpu.jogo_rodando(ex_com(TABELA)), "eden")

    def test_jogo_rodando_none_so_com_desktop(self):
        sem_eden = "\n".join(l for l in TABELA.splitlines() if "eden" not in l)
        self.assertIsNone(gpu.jogo_rodando(ex_com(sem_eden)))

    def test_jogo_aberto_traz_pid(self):
        self.assertEqual(gpu.jogo_aberto(ex_com(TABELA)), {"pid": 26589, "nome": "eden"})

    def test_sem_nvidia_smi_none(self):
        self.assertIsNone(gpu.jogo_rodando(ExecutorFalso({})))


if __name__ == "__main__":
    unittest.main()
