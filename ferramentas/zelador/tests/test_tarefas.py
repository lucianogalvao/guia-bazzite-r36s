import json
import tempfile
import time
import unittest
from pathlib import Path

from zelador.tarefas import Tarefas


def esperar_fim(t, id_, limite=5):
    fim = time.time() + limite
    while time.time() < fim:
        e = t.estado(id_)
        if e["situacao"] != "rodando":
            return e
        time.sleep(0.05)
    raise AssertionError("tarefa não terminou")


class TestTarefas(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())

    def test_sequencia_ok(self):
        t = Tarefas(self.dir)
        e = esperar_fim(t, t.iniciar("teste", [["true"], ["true"]]))
        self.assertEqual((e["situacao"], e["passo"], e["total"]), ("ok", 2, 2))

    def test_para_no_erro(self):
        x = self.dir / "nao-deve-existir"
        t = Tarefas(self.dir)
        e = esperar_fim(t, t.iniciar("teste", [["true"], ["false"], ["touch", str(x)]]))
        self.assertEqual(e["situacao"], "falhou")
        self.assertFalse(x.exists())

    def test_log_guarda_saida(self):
        t = Tarefas(self.dir)
        e = esperar_fim(t, t.iniciar("eco", [["echo", "olá zelador"]]))
        self.assertIn("olá zelador", e["log_fim"])

    def test_tarefa_sobrevive_sem_cliente(self):
        t = Tarefas(self.dir)
        id_ = t.iniciar("lenta", [["sleep", "0.3"], ["true"]])
        arq = self.dir / f"{id_}.json"
        fim = time.time() + 5
        while time.time() < fim and json.loads(arq.read_text())["situacao"] == "rodando":
            time.sleep(0.05)
        self.assertEqual(json.loads(arq.read_text())["situacao"], "ok")

    def test_interrompida_apos_reinicio(self):
        (self.dir / "abc.json").write_text(json.dumps(
            {"id": "abc", "titulo": "x", "passo": 1, "total": 3, "situacao": "rodando", "criada": 1}))
        t = Tarefas(self.dir)
        self.assertEqual(t.estado("abc")["situacao"], "interrompida")
        self.assertEqual(t.listar()[0]["id"], "abc")


if __name__ == "__main__":
    unittest.main()
