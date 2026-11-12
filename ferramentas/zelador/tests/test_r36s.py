import json
import re
import tempfile
import unittest
from pathlib import Path

from zelador import r36s
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
        self.mnt = Path(tempfile.mkdtemp()) / "EASYROMS"
        (self.mnt / "gba").mkdir(parents=True)
        (self.mnt / "bios").mkdir()

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
        info = r36s.detectar(lsblk(easyroms=str(self.mnt)))
        p = r36s.planejar_copia(["/x/j (USA).gba", "/x/j (USA).srm"], "gba", info)
        self.assertEqual([x["args"] for x in p], [["cp", "-n", "--", "/x/j (USA).gba", f"{self.mnt}/gba/"],
                                                   ["cp", "-n", "--", "/x/j (USA).srm", f"{self.mnt}/gba/"]])

    def test_copia_bios(self):
        info = r36s.detectar(lsblk(easyroms=str(self.mnt)))
        self.assertEqual(r36s.planejar_copia(["/x/scph1001.bin"], "bios", info)[0]["args"],
                         ["cp", "-n", "--", "/x/scph1001.bin", f"{self.mnt}/bios/"])

    def test_pasta_inexistente(self):
        info = r36s.detectar(lsblk(easyroms=str(self.mnt)))
        with self.assertRaises(ValueError) as c:
            r36s.planejar_copia(["/x/j.n64"], "n64", info)
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
