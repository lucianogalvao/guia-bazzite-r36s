import json
import tempfile
import time
import unittest
from pathlib import Path

from zelador.registro import Registro

DIA = 86400


class Relogio:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t


class TestRegistro(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.rel = Relogio(time.mktime((2026, 11, 12, 20, 0, 0, 0, 0, -1)))
        self.r = Registro(self.dir, agora=self.rel)

    def test_anotar_e_listar_mais_recente_primeiro(self):
        self.r.anotar("acao", "Reiniciar o streaming: ok")
        self.rel.t += 60
        self.r.anotar("chat", "Pergunta: oi", origem="192.168.0.5")
        itens = self.r.listar()
        self.assertEqual([i["tipo"] for i in itens], ["chat", "acao"])
        self.assertEqual(itens[0]["origem"], "192.168.0.5")
        self.assertIn("quando", itens[0])
        self.assertTrue((self.dir / "2026-11-12.jsonl").exists())

    def test_texto_longo_e_resumido(self):
        self.r.anotar("chat", "x" * 1000)
        self.assertLessEqual(len(self.r.listar()[0]["texto"]), 300)

    def test_apaga_dias_antigos(self):
        self.r.anotar("acao", "velho")
        self.rel.t += 8 * DIA
        self.r.anotar("acao", "novo")
        self.assertFalse((self.dir / "2026-11-12.jsonl").exists())
        self.assertEqual([i["texto"] for i in self.r.listar()], ["novo"])

    def test_mantem_sete_dias(self):
        for _ in range(7):
            self.r.anotar("acao", "dia")
            self.rel.t += DIA
        self.assertEqual(len(list(self.dir.glob("*.jsonl"))), 7)
        self.r.anotar("acao", "oitavo")
        self.assertEqual(len(list(self.dir.glob("*.jsonl"))), 7)

    def test_linha_corrompida_ignorada(self):
        self.r.anotar("acao", "ok")
        with (self.dir / "2026-11-12.jsonl").open("a") as f:
            f.write("{meia linha\n")
        self.assertEqual(len(self.r.listar()), 1)

    def test_limite(self):
        for i in range(20):
            self.r.anotar("acao", str(i))
        self.assertEqual([i["texto"] for i in self.r.listar(limite=3)], ["19", "18", "17"])


if __name__ == "__main__":
    unittest.main()
