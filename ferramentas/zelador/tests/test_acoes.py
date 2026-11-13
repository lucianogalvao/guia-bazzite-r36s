import unittest

from zelador import acoes
from zelador.executor import ExecutorFalso, Resultado

OK = Resultado(0, "", "")


def ex_base(extra=None):
    r = {
        ("systemctl", "--user", "restart"): OK,
        ("systemctl", "--user", "start"): OK,
        ("systemctl", "--user", "is-active"): Resultado(0, "active\n", ""),
        ("systemctl", "--user", "show"): Resultado(0, "Thu 2026-11-12 17:30:41 -03\n", ""),
        ("findmnt",): OK,
        ("df",): Resultado(0, "Avail\n858993459200\n", ""),
        ("nvidia-smi",): Resultado(0, "", ""),
    }
    r.update(extra or {})
    return ExecutorFalso(r)


class TestAcoes(unittest.TestCase):
    def test_reiniciar_ok(self):
        ex = ex_base()
        r = acoes.reiniciar_sunshine(ex, esperar=0)
        self.assertTrue(r["ok"])
        self.assertEqual(r["mensagem"], "Sunshine reiniciado e rodando.")
        self.assertIn(["systemctl", "--user", "restart", "app-dev.lizardbyte.app.Sunshine"], ex.chamadas)

    def test_reiniciar_falha(self):
        ex = ex_base({("systemctl", "--user", "is-active"): Resultado(3, "failed\n", "")})
        r = acoes.reiniciar_sunshine(ex, esperar=0)
        self.assertFalse(r["ok"])
        self.assertEqual(r["mensagem"], "O Sunshine não voltou. Veja o log em Status.")

    def test_status_disco_desmontado(self):
        ex = ex_base({("findmnt", "-rn", "/var/mnt/jogos"): Resultado(1, "", "")})
        s = acoes.status(ex)
        self.assertFalse(s["discos"]["/var/mnt/jogos"])
        self.assertTrue(s["discos"]["/var/mnt/roms"])
        self.assertEqual(s["sunshine"], "active")
        self.assertEqual(s["livre_gb"]["/var/mnt/roms"], 800.0)
        self.assertIsNone(s["jogo"])

    def test_backup_agora(self):
        ex = ex_base()
        r = acoes.backup_agora(ex)
        self.assertTrue(r["ok"])
        self.assertIn(["systemctl", "--user", "start", "--no-block", "backup-saves.service"], ex.chamadas)

    def test_desligar_agenda_poweroff(self):
        ex = ex_base({("sudo", "-n", "-l"): OK, ("sudo", "-n", "/usr/bin/systemctl"): OK})
        agendados = []
        r = acoes.desligar_pc(ex, atraso=3, agendar=lambda s, f: agendados.append((s, f)))
        self.assertTrue(r["ok"])
        self.assertIn(["sudo", "-n", "-l", "/usr/bin/systemctl", "poweroff"], ex.chamadas)
        self.assertNotIn(acoes.DESLIGAR, ex.chamadas)  # só depois do atraso
        self.assertEqual(agendados[0][0], 3)
        agendados[0][1]()
        self.assertIn(["sudo", "-n", "/usr/bin/systemctl", "poweroff"], ex.chamadas)

    def test_desligar_sem_regra_no_sudo(self):
        ex = ex_base({("sudo", "-n", "-l"): Resultado(1, "", "")})
        agendados = []
        r = acoes.desligar_pc(ex, agendar=lambda s, f: agendados.append(f))
        self.assertFalse(r["ok"])
        self.assertEqual(agendados, [])

    def test_acoes_registradas(self):
        self.assertEqual(set(acoes.ACOES), {"status", "reiniciar_sunshine", "backup_agora"})


if __name__ == "__main__":
    unittest.main()
