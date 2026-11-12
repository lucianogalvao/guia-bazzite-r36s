"""'O que está acontecendo?' sem modelo: regras tiradas dos capítulos 10 e 12 do guia."""
from __future__ import annotations

from . import acoes, config
from .executor import Executor


def coletar(ex: Executor) -> dict:
    log = ex.rodar(["journalctl", "--user", "-u", config.SUNSHINE_UNIT, "--since", "-15min", "-o", "cat", "-n", "60"])
    return {"status": acoes.status(ex), "log_sunshine": log.saida}


_LOG = [
    (("Couldn't find monitor", "Fatal"), "O Sunshine perdeu a tela (erro 503).", "reiniciar_sunshine"),
    (("Couldn't connect to Wayland display",),
     "O Sunshine foi iniciado no modo errado (Desktop × Game Mode).", "reiniciar_sunshine"),
    (("libx264 [software]",), "O stream está usando a CPU em vez da placa de vídeo.", None),
]


def regras(coleta: dict) -> list[dict]:
    st, log = coleta["status"], coleta.get("log_sunshine") or ""
    itens = []
    if st.get("sunshine") != "active":
        itens.append({"problema": "O Sunshine está parado.", "acao": "reiniciar_sunshine"})
    else:
        for marcas, problema, acao in _LOG:
            if any(m in log for m in marcas):
                itens.append({"problema": problema, "acao": acao})
    for disco, montado in st.get("discos", {}).items():
        if not montado:
            itens.append({"problema": f"Disco {disco} não está montado.", "acao": None})
    return itens


def resumo(itens: list[dict]) -> str:
    if not itens:
        return "Não achei nada de errado no PC. Se o erro é na TV, tente reiniciar o Sunshine."
    return " ".join(i["problema"] for i in itens)
