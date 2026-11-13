"""Botões: comandos fixos, os mesmos de docs/bazzite/12-comandos.md."""
from __future__ import annotations

import threading
import time
from typing import Callable

from . import config, gpu
from .executor import Executor


def status(ex: Executor) -> dict:
    discos, livre = {}, {}
    for d in config.DISCOS:
        discos[d] = ex.rodar(["findmnt", "-rn", d]).codigo == 0
        r = ex.rodar(["df", "-B1", "--output=avail", d])
        linhas = r.saida.split()
        livre[d] = round(int(linhas[-1]) / 2**30, 1) if r.codigo == 0 and linhas[-1:] and linhas[-1].isdigit() else None
    sun = ex.rodar(["systemctl", "--user", "is-active", config.SUNSHINE_UNIT]).saida.strip() or "desconhecido"
    bkp = ex.rodar(["systemctl", "--user", "show", config.BACKUP_UNIT, "-p", "ExecMainExitTimestamp", "--value"])
    return {
        "discos": discos,
        "livre_gb": livre,
        "sunshine": sun,
        "jogo": gpu.jogo_rodando(ex),
        "ultimo_backup": bkp.saida.strip() or None,
    }


def reiniciar_sunshine(ex: Executor, esperar: float = 3) -> dict:
    ex.rodar(["systemctl", "--user", "restart", config.SUNSHINE_UNIT], timeout=60)
    time.sleep(esperar)
    ativo = ex.rodar(["systemctl", "--user", "is-active", config.SUNSHINE_UNIT]).saida.strip() == "active"
    msg = "Sunshine reiniciado e rodando." if ativo else "O Sunshine não voltou. Veja o log em Status."
    return {"ok": ativo, "mensagem": msg}


def backup_agora(ex: Executor) -> dict:
    r = ex.rodar(["systemctl", "--user", "start", "--no-block", config.BACKUP_UNIT])
    ok = r.codigo == 0
    return {"ok": ok, "mensagem": "Backup dos saves iniciado." if ok else "Não consegui iniciar o backup."}


DESLIGAR = ["sudo", "-n", "/usr/bin/systemctl", "poweroff"]


def _agendar(segundos: float, f: Callable[[], object]) -> None:
    t = threading.Timer(segundos, f)
    t.daemon = True
    t.start()


def desligar_pc(ex: Executor, atraso: float = 3, agendar: Callable = _agendar) -> dict:
    """Confere a regra do sudoers (poweroff sem senha) e desliga daqui a `atraso` s,
    para a resposta chegar ao celular antes da rede cair."""
    pode = ex.rodar(["sudo", "-n", "-l", *DESLIGAR[2:]]).codigo == 0
    if not pode:
        return {"ok": False, "mensagem": "O sudo não deixa o Zelador desligar o PC (falta a regra do poweroff)."}
    agendar(atraso, lambda: ex.rodar(DESLIGAR, timeout=60))
    return {"ok": True, "mensagem": "Desligando o PC. A página vai perder contato em instantes."}


ACOES: dict[str, Callable[[Executor], dict]] = {
    "status": status,
    "reiniciar_sunshine": reiniciar_sunshine,
    "backup_agora": backup_agora,
}
