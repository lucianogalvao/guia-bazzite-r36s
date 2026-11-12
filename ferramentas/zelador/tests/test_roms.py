import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zelador import config, roms
from zelador.executor import ExecutorFalso, Resultado


def bencode(v):
    if isinstance(v, int):
        return b"i%de" % v
    if isinstance(v, str):
        v = v.encode()
    if isinstance(v, bytes):
        return b"%d:%s" % (len(v), v)
    if isinstance(v, list):
        return b"l" + b"".join(bencode(x) for x in v) + b"e"
    return b"d" + b"".join(bencode(k) + bencode(x) for k, x in sorted(v.items())) + b"e"


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.roms, self.sw, self.ex = self.tmp / "roms", self.tmp / "switch", self.tmp / "extras"
        (self.roms / "snes").mkdir(parents=True)
        self.p = mock.patch.multiple(config, ROMS=self.roms, SWITCH=self.sw, SWITCH_EXTRAS=self.ex)
        self.p.start()
        self.addCleanup(self.p.stop)


class TestTorrents(Base):
    def test_torrents_ativos_le_fastresume(self):
        bt = self.tmp / "bt"
        bt.mkdir()
        (bt / "a.fastresume").write_bytes(bencode(
            {"save_path": "/var/mnt/roms/Downloads", "name": "Jogo A (World)", "pieces": b"\x00\xff", "paused": 0}))
        (bt / "b.fastresume").write_bytes(bencode({"save_path": "/home/u/Downloads", "qBt-name": "Jogo B"}))
        self.assertEqual(roms.torrents_ativos(bt), {
            Path("/var/mnt/roms/Downloads/Jogo A (World)"), Path("/home/u/Downloads/Jogo B")})

    def test_torrents_pasta_inexistente(self):
        self.assertEqual(roms.torrents_ativos(self.tmp / "nao-existe"), set())

    def test_protegido_dentro_da_pasta(self):
        ativos = {Path("/d/Jogo A")}
        self.assertTrue(roms.protegido(Path("/d/Jogo A/x.7z"), ativos))
        self.assertTrue(roms.protegido(Path("/d/Jogo A"), ativos))
        self.assertFalse(roms.protegido(Path("/d/Jogo AB/x.7z"), ativos))


class TestListar(Base):
    def test_listar_ignora_lixo_e_mostra_conteudo(self):
        d = self.tmp / "dl" / "Jogo (USA)"
        d.mkdir(parents=True)
        (d / "Jogo (USA).7z").write_bytes(b"0" * (6 * 2**20))
        (d / "pequeno.sfc").write_bytes(b"0" * 10)
        (d / "metadata.json").write_bytes(b"0" * (6 * 2**20))
        ex = ExecutorFalso({("7z", "l"): Resultado(0, "Path = Jogo (USA).bin\nSize = 1\nPath = Jogo (USA).cue\n", "")})
        itens = roms.listar_downloads(ex, self.tmp / "dl", ativos=set())
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["conteudo"], ["Jogo (USA).bin", "Jogo (USA).cue"])
        self.assertEqual(itens[0]["mib"], 6)
        self.assertFalse(itens[0]["protegido"])


class TestPlano(Base):
    def test_plano_7z_switch_base(self):
        p = roms.planejar([{"origem": "/dl/Jogo/Jogo (World).7z", "sistema": "switch", "tipo": "base"}])
        self.assertEqual(p[-1]["args"], ["7z", "x", "-y", "-aos", f"-o{self.sw}", "/dl/Jogo/Jogo (World).7z"])
        self.assertFalse(any(x["apaga"] for x in p))

    def test_plano_extra_vai_para_extras(self):
        p = roms.planejar([{"origem": "/dl/Super Mario Odyssey (World) (Rev 3)/upd (Update).nsp",
                            "sistema": "switch", "tipo": "extra"}])
        destino = self.ex / "Super Mario Odyssey"
        self.assertEqual(p[0]["args"], ["mkdir", "-p", str(destino)])
        self.assertEqual(p[1]["args"], ["mv", "-n", "/dl/Super Mario Odyssey (World) (Rev 3)/upd (Update).nsp",
                                         str(destino / "upd (Update).nsp")])

    def test_plano_extra_com_jogo_explicito(self):
        p = roms.planejar([{"origem": "/dl/X_NSW/u.nsp", "sistema": "switch", "tipo": "extra", "jogo": "Pokemon Z-A"}])
        self.assertEqual(p[0]["args"], ["mkdir", "-p", str(self.ex / "Pokemon Z-A")])

    def test_plano_solto_ativo_copia(self):
        p = roms.planejar([{"origem": "/dl/T/j.sfc", "sistema": "snes", "tipo": "base"}], ativos={Path("/dl/T")})
        self.assertEqual(p[-1]["args"], ["cp", "-n", "/dl/T/j.sfc", str(self.roms / "snes" / "j.sfc")])

    def test_plano_sistema_inexistente_recusa(self):
        with self.assertRaises(ValueError) as c:
            roms.planejar([{"origem": "/dl/j.xyz", "sistema": "naoexiste", "tipo": "base"}])
        self.assertIn("naoexiste", str(c.exception))

    def test_plano_com_nome_estranho(self):
        o = "/x/Super Mario Galaxy [010099C022B96000][v0] + 2, (En,Ja) 'a'.7z"
        p = roms.planejar([{"origem": o, "sistema": "switch", "tipo": "base"}])
        self.assertEqual(p[-1]["args"][-1], o)
        self.assertEqual(p[-1]["args"].count(o), 1)


if __name__ == "__main__":
    unittest.main()
