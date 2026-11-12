"""Caminhos e constantes. Cada um pode ser trocado pela variável ZELADOR_<NOME>."""
from __future__ import annotations

import os
from pathlib import Path


def _env(nome: str, padrao):
    v = os.environ.get(f"ZELADOR_{nome}")
    if v is None:
        return padrao
    return Path(v) if isinstance(padrao, Path) else type(padrao)(v)


PORTA = _env("PORTA", 8787)
OLLAMA_URL = _env("OLLAMA_URL", "http://127.0.0.1:11434")
MODELO = _env("MODELO", "qwen3:8b")
KEEP_ALIVE = _env("KEEP_ALIVE", "5m")
SUNSHINE_UNIT = _env("SUNSHINE_UNIT", "app-dev.lizardbyte.app.Sunshine")
BACKUP_UNIT = _env("BACKUP_UNIT", "backup-saves.service")
DOWNLOADS = _env("DOWNLOADS", Path("/var/mnt/roms/Downloads"))
ROMS = _env("ROMS", Path("/var/mnt/roms/Emulation/roms"))
SWITCH = _env("SWITCH", Path("/var/mnt/jogos/Emulation/roms/switch"))
SWITCH_EXTRAS = _env("SWITCH_EXTRAS", Path("/var/mnt/jogos/Emulation/switch-extras"))
QBT_BACKUP = _env(
    "QBT_BACKUP",
    Path.home() / ".var/app/org.qbittorrent.qBittorrent/data/qBittorrent/BT_backup",
)
ESTADO = _env("ESTADO", Path.home() / ".local/state/zelador")
DISCOS = ("/var/mnt/roms", "/var/mnt/jogos")
