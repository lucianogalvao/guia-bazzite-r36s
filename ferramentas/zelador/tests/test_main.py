import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


class TestMain(unittest.TestCase):
    def rodar(self, *args, entrada=""):
        env = dict(os.environ, ZELADOR_ESTADO=self.estado)
        return subprocess.run([sys.executable, "-m", "zelador", *args], cwd=RAIZ, env=env, input=entrada,
                              capture_output=True, text=True, timeout=20)

    def setUp(self):
        self.estado = tempfile.mkdtemp()

    def test_definir_pin_pela_entrada(self):
        r = self.rodar("definir-pin", entrada="4321\n4321\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((Path(self.estado) / "pin").exists())

    def test_definir_pin_diferentes(self):
        r = self.rodar("definir-pin", entrada="4321\n1111\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("não conferem", r.stderr)

    def test_comando_desconhecido(self):
        self.assertNotEqual(self.rodar("xyz").returncode, 0)


if __name__ == "__main__":
    unittest.main()
