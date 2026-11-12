"""python3 -m zelador servir | definir-pin"""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from . import config
from .auth import Auth
from .executor import Executor, ExecutorFalso, Resultado

WEB = Path(__file__).resolve().parents[1] / "web"


def _ler(pergunta: str) -> str:
    if sys.stdin.isatty():
        return getpass.getpass(pergunta)
    return sys.stdin.readline().strip()


def _executor_demo() -> Executor:
    tabela = "|    0   N/A  N/A   26589    C+G   /x/bin/eden        746MiB |\n"
    lsblk = ('{"blockdevices":[{"name":"sdc","label":null,"fstype":null,"mountpoint":null,"tran":"usb",'
             '"children":[{"name":"sdc1","label":"BOOT","fstype":"vfat","mountpoint":"/tmp","tran":null},'
             '{"name":"sdc2","label":"ROOTFS","fstype":"btrfs","mountpoint":null,"tran":null},'
             '{"name":"sdc3","label":"EASYROMS","fstype":"exfat","mountpoint":"/tmp","tran":null}]}]}')
    return ExecutorFalso({
        ("systemctl", "--user", "is-active"): Resultado(3, "inactive\n", ""),
        ("systemctl",): Resultado(0, "", ""),
        ("findmnt",): Resultado(0, "", ""),
        ("df",): Resultado(0, "Avail\n858993459200\n", ""),
        ("nvidia-smi",): Resultado(0, tabela, ""),
        ("journalctl",): Resultado(0, "Error: Couldn't find monitor\n", ""),
        ("lsblk",): Resultado(0, lsblk, ""),
    })


def main(argv: list[str]) -> int:
    cmd = argv[1] if len(argv) > 1 else "servir"
    if cmd == "definir-pin":
        pin = _ler("Novo PIN (4 a 6 números): ")
        if pin != _ler("Repita o PIN: "):
            print("Os PINs não conferem.", file=sys.stderr)
            return 1
        try:
            Auth(config.ESTADO).definir_pin(pin)
        except ValueError as e:
            print(e, file=sys.stderr)
            return 1
        print("PIN definido. As sessões antigas foram desconectadas.")
        return 0
    if cmd == "servir":
        from .servidor import criar_servidor
        demo = os.environ.get("ZELADOR_FALSO") == "1"
        ex = _executor_demo() if demo else Executor()
        if demo:
            Auth(config.ESTADO).definir_pin("0000")
        srv = criar_servidor(("0.0.0.0", config.PORTA), ex, config.ESTADO, WEB)
        print(f"Zelador em http://0.0.0.0:{config.PORTA}" + (" (demonstração, PIN 0000)" if demo else ""))
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return 0
    print("Uso: python3 -m zelador [servir|definir-pin]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
