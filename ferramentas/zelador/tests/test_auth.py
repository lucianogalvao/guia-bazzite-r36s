import tempfile
import unittest
from pathlib import Path

from zelador.auth import Auth, Bloqueado


class Relogio:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class TestAuth(unittest.TestCase):
    def setUp(self):
        self.relogio = Relogio()
        self.auth = Auth(Path(tempfile.mkdtemp()), relogio=self.relogio)
        self.auth.definir_pin("123456")

    def errar(self, vezes, ip="10.0.0.9"):
        for _ in range(vezes):
            self.assertFalse(self.auth.conferir("000000", ip))

    def test_pin_precisa_de_6_numeros(self):
        for ruim in ("1234", "12345", "1234567", "12345a", ""):
            with self.assertRaises(ValueError):
                self.auth.definir_pin(ruim)

    def test_pin_certo(self):
        self.assertTrue(self.auth.conferir("123456", "10.0.0.9"))

    def test_bloqueio_cresce_a_cada_erro(self):
        self.errar(5)
        with self.assertRaises(Bloqueado) as c:
            self.auth.conferir("123456", "10.0.0.9")
        self.assertEqual(c.exception.segundos, 60)
        esperas = []
        for _ in range(3):
            self.relogio.t += c.exception.segundos
            self.errar(1)
            with self.assertRaises(Bloqueado) as c:
                self.auth.conferir("123456", "10.0.0.9")
            esperas.append(c.exception.segundos)
        self.assertEqual(esperas, [120, 240, 480])

    def test_bloqueio_tem_teto_de_uma_hora(self):
        self.errar(5)
        for _ in range(20):
            self.relogio.t += 3600
            self.errar(1)
        with self.assertRaises(Bloqueado) as c:
            self.auth.conferir("123456", "10.0.0.9")
        self.assertEqual(c.exception.segundos, 3600)

    def test_bloqueio_e_por_aparelho(self):
        self.errar(5, ip="10.0.0.66")
        with self.assertRaises(Bloqueado):
            self.auth.conferir("123456", "10.0.0.66")
        self.assertTrue(self.auth.conferir("123456", "10.0.0.9"))

    def test_acerto_zera_os_erros(self):
        self.errar(4)
        self.assertTrue(self.auth.conferir("123456", "10.0.0.9"))
        self.errar(4)
        self.assertTrue(self.auth.conferir("123456", "10.0.0.9"))


if __name__ == "__main__":
    unittest.main()
