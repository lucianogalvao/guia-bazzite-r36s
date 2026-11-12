import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zelador import config, ferramentas
from zelador.executor import ExecutorFalso, Resultado
from zelador.propostas import Propostas
from zelador.tarefas import Tarefas

NOMES = {"propor_fechar_jogo", "status", "diagnosticar", "ler_log", "reiniciar_sunshine", "listar_downloads", "propor_organizacao",
         "propor_apagar", "r36s_info", "propor_copia_r36s", "propor_ejetar_r36s"}


class TestFerramentas(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        self.dl = d / "Downloads"
        (self.dl / "Jogo A").mkdir(parents=True)
        self.p = mock.patch.multiple(config, DOWNLOADS=self.dl, SWITCH_EXTRAS=d / "extras", ROMS=d / "roms",
                                     SWITCH=d / "switch")
        self.p.start()
        self.addCleanup(self.p.stop)
        self.props = Propostas(d / "propostas", Tarefas(d / "tarefas"))
        ex = ExecutorFalso({("journalctl",): Resultado(0, "linha1\nlinha2\n", "")})
        self.ex = ex
        self.ativos_extra = set()
        self.lista, self.chamar = ferramentas.criar_registro(
            ex, self.props, ativos=lambda: {self.dl / "Jogo A"} | self.ativos_extra)

    def test_registro_nomes(self):
        self.assertEqual({f["function"]["name"] for f in self.lista}, NOMES)
        for f in self.lista:
            self.assertEqual(f["type"], "function")
            self.assertEqual(f["function"]["parameters"]["type"], "object")

    def test_ferramenta_desconhecida(self):
        self.assertEqual(self.chamar("rm_rf", {}), {"erro": "Ferramenta não existe."})

    def test_ler_log_limita_linhas(self):
        self.chamar("ler_log", {"servico": "sunshine", "linhas": 5000})
        self.assertIn("200", self.ex.chamadas[-1])
        self.assertIn(config.SUNSHINE_UNIT, self.ex.chamadas[-1])

    def test_ler_log_servico_invalido(self):
        self.assertIn("erro", self.chamar("ler_log", {"servico": "sshd"}))

    def test_propor_apagar_recusa_torrent_ativo(self):
        r = self.chamar("propor_apagar", {"caminhos": [str(self.dl / "Jogo A" / "a.7z")]})
        self.assertIn("erro", r)
        self.assertIn("semeando", r["erro"])
        self.assertEqual(self.props.pendentes(), [])

    def test_propor_apagar_recusa_fora_das_pastas(self):
        r = self.chamar("propor_apagar", {"caminhos": ["/var/mnt/roms/Emulation/saves/x"]})
        self.assertIn("erro", r)
        r = self.chamar("propor_apagar", {"caminhos": [str(self.dl / ".." / "fora")]})
        self.assertIn("erro", r)

    def test_propor_apagar_cria_proposta_que_apaga(self):
        alvo = self.dl / "Jogo B" / "b.7z"
        r = self.chamar("propor_apagar", {"caminhos": [str(alvo)]})
        p = self.props.pendentes()[0]
        self.assertEqual(r["proposta"], p["id"])
        self.assertEqual(p["passos"][0]["args"], ["rm", "--", str(alvo)])
        self.assertTrue(p["passos"][0]["apaga"])

    def test_propor_apagar_recusa_symlink_para_fora(self):
        fora = self.dl.parent / "fora"
        fora.mkdir()
        (self.dl / "link").symlink_to(fora)
        self.assertIn("erro", self.chamar("propor_apagar", {"caminhos": [str(self.dl / "link" / "a.sav")]}))
        self.assertIn("erro", self.chamar("propor_apagar", {"caminhos": [str(self.dl / "link")]}))

    def test_excecao_inesperada_vira_erro(self):
        self.assertIn("erro", self.chamar("ler_log", {"servico": "sunshine", "linhas": float("inf")}))

    def test_apagar_revalida_ao_aprovar(self):
        alvo = self.dl / "Jogo C" / "c.7z"
        r = self.chamar("propor_apagar", {"caminhos": [str(alvo)]})
        self.ativos_extra.add(self.dl / "Jogo C")
        res = self.props.aprovar(r["proposta"], confirmar_apagar=True)
        self.assertFalse(res["ok"])
        self.assertIn("semeando", res["mensagem"])

    def test_propor_fechar_jogo(self):
        self.ex.respostas[("nvidia-smi",)] = Resultado(0, "|    0   N/A  N/A   26589    C+G   /x/bin/eden   746MiB |\n", "")
        r = self.chamar("propor_fechar_jogo", {})
        p = self.props.pendentes()[0]
        self.assertEqual(r["proposta"], p["id"])
        self.assertEqual(p["passos"][0]["args"], ["kill", "-TERM", "26589"])
        self.assertIn("eden", p["passos"][0]["descricao"])
        self.assertIn("não foi salvo", p["passos"][0]["descricao"])

    def test_fechar_sem_jogo_aberto(self):
        self.ex.respostas[("nvidia-smi",)] = Resultado(0, "", "")
        self.assertEqual(self.chamar("propor_fechar_jogo", {}), {"erro": "Nenhum jogo aberto."})

    def test_fechar_jogo_recusa_se_outro_jogo(self):
        self.ex.respostas[("nvidia-smi",)] = Resultado(0, "|    0   N/A  N/A   26589    C+G   /x/bin/eden   746MiB |\n", "")
        r = self.chamar("propor_fechar_jogo", {})
        self.ex.respostas[("nvidia-smi",)] = Resultado(0, "|    0   N/A  N/A   30000    G   /x/bin/pcsx2   900MiB |\n", "")
        res = self.props.aprovar(r["proposta"])
        self.assertFalse(res["ok"])
        self.assertIn("mudou", res["mensagem"])

    def test_erro_de_valor_vira_mensagem(self):
        r = self.chamar("propor_organizacao", {"itens": [{"origem": "/x.sfc", "sistema": "nada", "tipo": "base"}]})
        self.assertIn("erro", r)


if __name__ == "__main__":
    unittest.main()
