import unittest

from zelador import diagnostico


def coleta(sunshine="active", log="", discos=None):
    return {
        "status": {"sunshine": sunshine, "discos": discos or {"/var/mnt/roms": True, "/var/mnt/jogos": True}},
        "log_sunshine": log,
    }


class TestRegras(unittest.TestCase):
    def test_sunshine_parado(self):
        itens = diagnostico.regras(coleta(sunshine="inactive"))
        self.assertEqual(itens[0], {"problema": "O Sunshine está parado.", "acao": "reiniciar_sunshine"})

    def test_perdeu_a_tela(self):
        itens = diagnostico.regras(coleta(log="Error: Couldn't find monitor [DP-3]"))
        self.assertEqual(itens, [{"problema": "O Sunshine perdeu a tela (erro 503).", "acao": "reiniciar_sunshine"}])

    def test_modo_errado(self):
        itens = diagnostico.regras(coleta(log="Couldn't connect to Wayland display: gamescope-0"))
        self.assertEqual(itens[0]["acao"], "reiniciar_sunshine")
        self.assertIn("modo errado", itens[0]["problema"])

    def test_encoder_cpu(self):
        itens = diagnostico.regras(coleta(log="Found H.264 encoder: libx264 [software]"))
        self.assertEqual(itens, [{"problema": "O stream está usando a CPU em vez da placa de vídeo.", "acao": None}])

    def test_disco_desmontado(self):
        itens = diagnostico.regras(coleta(discos={"/var/mnt/roms": True, "/var/mnt/jogos": False}))
        self.assertEqual(itens, [{"problema": "Disco /var/mnt/jogos não está montado.", "acao": None}])

    def test_sem_problemas(self):
        self.assertEqual(diagnostico.regras(coleta()), [])
        self.assertEqual(
            diagnostico.resumo([]),
            "Não achei nada de errado no PC. Se o erro é na TV, tente reiniciar o Sunshine.",
        )

    def test_ordem_sunshine_parado_primeiro(self):
        itens = diagnostico.regras(coleta(sunshine="failed", log="Fatal: something"))
        self.assertEqual(itens[0]["problema"], "O Sunshine está parado.")


if __name__ == "__main__":
    unittest.main()
