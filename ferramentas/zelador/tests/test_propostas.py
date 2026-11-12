import tempfile
import threading
import time
import unittest
from pathlib import Path

from zelador.propostas import Propostas
from zelador.tarefas import Tarefas


class TestPropostas(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        self.alvo = d / "feito"
        self.tarefas = Tarefas(d / "tarefas")
        self.p = Propostas(d / "propostas", self.tarefas)

    def test_aprovar_duas_vezes_executa_uma(self):
        id_ = self.p.criar("x", [{"descricao": "d", "args": ["touch", str(self.alvo)], "apaga": False}])
        res = []
        ts = [threading.Thread(target=lambda: res.append(self.p.aprovar(id_))) for _ in range(5)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertEqual(sum(1 for r in res if r["ok"]), 1)
        self.assertEqual(len(self.tarefas.listar()), 1)
        self.assertIn({"ok": False, "mensagem": "Proposta não existe ou já foi aprovada."}, res)

    def test_apagar_exige_confirmacao(self):
        id_ = self.p.criar("apagar", [{"descricao": "d", "args": ["rm", "--", "/x"], "apaga": True}])
        self.assertEqual(self.p.aprovar(id_), {"ok": False, "precisa_confirmar_apagar": True})
        self.assertEqual(self.p.pendentes()[0]["id"], id_)

    def test_recusar_remove(self):
        id_ = self.p.criar("x", [])
        self.p.recusar(id_)
        self.assertEqual(self.p.pendentes(), [])
        self.assertFalse(self.p.aprovar(id_)["ok"])

    def test_persiste_entre_instancias(self):
        id_ = self.p.criar("x", [{"descricao": "d", "args": ["true"], "apaga": False}])
        outra = Propostas(self.p.dir, self.tarefas)
        self.assertEqual(outra.pendentes()[0]["id"], id_)


if __name__ == "__main__":
    unittest.main()
