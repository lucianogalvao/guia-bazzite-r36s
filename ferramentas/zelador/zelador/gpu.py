"""Quem está usando a placa de vídeo (para saber se há jogo aberto)."""
from __future__ import annotations

import re

from .executor import Executor

IGNORAR = {"sunshine", "kwin_wayland", "plasmashell", "Xwayland", "steam", "steamwebhelper",
           "es-de", "firefox", "gamescope", "ollama"}
LIMITE_MIB = 300

# |    0   N/A  N/A   26589    C+G   ...16050999093682512908/bin/eden   746MiB |
_LINHA = re.compile(r"^\|\s+\d+\s+\S+\s+\S+\s+(\d+)\s+(?:C\+G|C|G)\s+(\S+)\s+(\d+)MiB\s+\|$")


def processos(ex: Executor) -> list[dict]:
    """Lê a tabela 'Processes' do nvidia-smi (lista processos C e G; jogos são G)."""
    r = ex.rodar(["nvidia-smi"])
    if r.codigo != 0:
        return []
    ps = []
    for linha in r.saida.splitlines():
        m = _LINHA.match(linha.strip())
        if m:
            ps.append({"pid": int(m[1]), "nome": m[2].rsplit("/", 1)[-1], "mib": int(m[3])})
    return ps


def jogo_rodando(ex: Executor) -> str | None:
    for p in processos(ex):
        if p["mib"] >= LIMITE_MIB and p["nome"] not in IGNORAR:
            return p["nome"]
    return None
