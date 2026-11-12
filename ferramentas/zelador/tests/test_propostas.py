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

    def test_expira_apos_1h(self):
        id_ = self.p.criar("x", [{"descricao": "d", "args": ["true"], "apaga": False}])
        arq = self.p.dir / f"{id_}.json"
        import json
        d = json.loads(arq.read_text()); d["criada"] -= 3601; arq.write_text(json.dumps(d))
        r = self.p.aprovar(id_)
        self.assertFalse(r["ok"])
        self.assertIn("expirou", r["mensagem"])

    def test_refaz_e_recusa_se_mudou(self):
        estado = {"n": 1}
        self.p.refazedores["teste"] = lambda entrada: [{"descricao": str(estado["n"]), "args": ["true"], "apaga": False}]
        id_ = self.p.criar("x", [{"descricao": "1", "args": ["true"], "apaga": False}], refazer="teste", entrada={})
        estado["n"] = 2
        r = self.p.aprovar(id_)
        self.assertFalse(r["ok"])
        self.assertIn("mudou", r["mensagem"])

    def test_refaz_com_erro_recusa(self):
        def falha(entrada):
            raise ValueError("Cartão do R36S não encontrado.")
        self.p.refazedores["r"] = falha
        id_ = self.p.criar("x", [], refazer="r", entrada={})
        self.assertEqual(self.p.aprovar(id_), {"ok": False, "mensagem": "Cartão do R36S não encontrado."})

    def test_pendentes_ignora_arquivo_corrompido(self):
        (self.p.dir / "ruim.json").write_text("{meio")
        self.p.criar("x", [])
        self.assertEqual(len(self.p.pendentes()), 1)

    def test_persiste_entre_instancias(self):
        id_ = self.p.criar("x", [{"descricao": "d", "args": ["true"], "apaga": False}])
        outra = Propostas(self.p.dir, self.tarefas)
        self.assertEqual(outra.pendentes()[0]["id"], id_)


if __name__ == "__main__":
    unittest.main()
