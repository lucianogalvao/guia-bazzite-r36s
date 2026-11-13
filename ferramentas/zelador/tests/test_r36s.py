import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from zelador import config, r36s
from zelador.executor import ExecutorFalso, Resultado


def lsblk(easyroms=None, rootfs=None, boot=None, usb=True):
    filhos = [
        {"name": "sdc1", "label": "BOOT", "fstype": "vfat", "mountpoint": boot, "tran": None},
        {"name": "sdc2", "label": "ROOTFS", "fstype": "btrfs", "mountpoint": rootfs, "tran": None},
        {"name": "sdc3", "label": "EASYROMS", "fstype": "exfat", "mountpoint": easyroms, "tran": None},
    ]
    d = {"blockdevices": [
        {"name": "sda", "label": None, "fstype": None, "mountpoint": None, "tran": "sata",
         "children": [{"name": "sda3", "label": None, "fstype": "btrfs", "mountpoint": "/var/home", "tran": None}]},
        {"name": "sdc", "label": None, "fstype": None, "mountpoint": None, "tran": "usb" if usb else "sata",
         "children": filhos},
    ]}
    return ExecutorFalso({
        ("lsblk",): Resultado(0, json.dumps(d), ""),
        ("df",): Resultado(0, "Avail\n10737418240\n", ""),
    })


class TestR36S(unittest.TestCase):
    def setUp(self):
        raiz = Path(tempfile.mkdtemp())
        self.mnt = raiz / "EASYROMS"
        (self.mnt / "gba").mkdir(parents=True)
        (self.mnt / "bios").mkdir()
        self.dl = raiz / "Downloads"
        self.dl.mkdir()
        self.roms = raiz / "Emulation" / "roms"
        (raiz / "Emulation" / "bios").mkdir(parents=True)
        self.roms.mkdir()
        for nome in ("j (USA).gba", "j (USA).srm", "j.n64"):
            (self.dl / nome).write_text("x")
        (raiz / "Emulation" / "bios" / "scph1001.bin").write_text("x")
        self.segredo = raiz / "rclone.conf"
        self.segredo.write_text("token")
        p = mock.patch.multiple(config, DOWNLOADS=self.dl, ROMS=self.roms)
        p.start()
        self.addCleanup(p.stop)
        self.info = r36s.detectar(lsblk(easyroms=str(self.mnt)))

    def assertRecusa(self, arquivos, sistema, trecho):
        with self.assertRaises(ValueError) as c:
            r36s.planejar_copia([str(a) for a in arquivos], sistema, self.info)
        self.assertIn(trecho, str(c.exception))

    def test_recusa_sistema_com_ponto_ponto(self):
        (self.mnt.parent / "fora").mkdir()
        self.assertRecusa([self.dl / "j (USA).gba"], "../fora", "Nome inválido")
        self.assertRecusa([self.dl / "j (USA).gba"], "gba/../..", "Nome inválido")

    def test_recusa_pasta_do_cartao_que_e_link_para_fora(self):
        (self.mnt.parent / "fora").mkdir()
        (self.mnt / "psx").symlink_to(self.mnt.parent / "fora")
        self.assertRecusa([self.dl / "j (USA).gba"], "psx", "fora do cartão")

    def test_recusa_origem_fora_de_downloads_e_emulation(self):
        self.assertRecusa([self.segredo], "gba", "Só copio")

    def test_recusa_origem_link(self):
        (self.dl / "isca.gba").symlink_to(self.segredo)
        self.assertRecusa([self.dl / "isca.gba"], "gba", "Só copio")

    def test_recusa_origem_com_ponto_ponto(self):
        self.assertRecusa([f"{self.dl}/../rclone.conf"], "gba", "Só copio")

    def test_recusa_origem_inexistente_ou_pasta(self):
        self.assertRecusa([self.dl / "nada.gba"], "gba", "Só copio")
        self.assertRecusa([self.dl], "gba", "Só copio")

    def test_detecta_cartao(self):
        info = r36s.detectar(lsblk(easyroms=str(self.mnt), boot="/run/media/u/BOOT"))
        self.assertEqual(info, {"presente": True, "easyroms": str(self.mnt), "boot": "/run/media/u/BOOT",
                                "rootfs_montado": False, "livre_gb": 10.0})

    def test_sem_cartao(self):
        info = r36s.detectar(lsblk(easyroms=str(self.mnt), usb=False))
        self.assertFalse(info["presente"])
        with self.assertRaises(ValueError) as c:
            r36s.planejar_copia(["/x/j.gba"], "gba", info)
        self.assertEqual(str(c.exception), "Cartão do R36S não encontrado.")

    def test_recusa_com_rootfs_montado(self):
        info = r36s.detectar(lsblk(easyroms=str(self.mnt), rootfs="/run/media/u/ROOTFS"))
        self.assertTrue(info["rootfs_montado"])
        with self.assertRaises(ValueError) as c:
            r36s.planejar_copia(["/x/j.gba"], "gba", info)
        self.assertEqual(str(c.exception),
                         "A partição de sistema (ROOTFS) do cartão está montada. Desmonte antes: isso pode estragar o R36S.")

    def test_copia_jogo_e_save(self):
        a, b = str(self.dl / "j (USA).gba"), str(self.dl / "j (USA).srm")
        p = r36s.planejar_copia([a, b], "gba", self.info)
        self.assertEqual([x["args"] for x in p], [["cp", "-n", "--", a, f"{self.mnt}/gba/"],
                                                   ["cp", "-n", "--", b, f"{self.mnt}/gba/"]])

    def test_copia_bios(self):
        bios = str(self.roms.parent / "bios" / "scph1001.bin")
        self.assertEqual(r36s.planejar_copia([bios], "bios", self.info)[0]["args"],
                         ["cp", "-n", "--", bios, f"{self.mnt}/bios/"])

    def test_pasta_inexistente(self):
        with self.assertRaises(ValueError) as c:
            r36s.planejar_copia([str(self.dl / "j.n64")], "n64", self.info)
        self.assertEqual(str(c.exception), "Pasta n64 não existe no cartão.")

    def test_ejetar(self):
        info = r36s.detectar(lsblk(easyroms=str(self.mnt), boot="/run/media/u/BOOT"))
        self.assertEqual([x["args"] for x in r36s.passos_ejetar(info)],
                         [["sync"], ["umount", str(self.mnt)], ["umount", "/run/media/u/BOOT"]])

    def test_fonte_sem_mount(self):
        fonte = (Path(r36s.__file__)).read_text().replace("umount", "")
        self.assertIsNone(re.search(r"[\"']mount[\"']", fonte))


if __name__ == "__main__":
    unittest.main()
