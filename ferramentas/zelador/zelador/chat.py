"""Chat com o modelo local (Ollama). O modelo só age por ferramentas do registro."""
from __future__ import annotations

import json
import socket
import urllib.request
from typing import Callable
from urllib.error import URLError

from . import gpu
from .executor import Executor

SISTEMA = ("Você é o Zelador do PC console da casa. Responda em português do Brasil, curto e simples. "
           "Use só as ferramentas disponíveis. Nunca diga que fez algo sem ter chamado a ferramenta. "
           "Ações que mudam arquivos viram uma proposta que a pessoa aprova na tela: diga isso. "
           "Se o pedido não couber nas ferramentas, responda: 'Não sei fazer isso. Peça ao Claude.'")
INDISPONIVEL = "O modelo está indisponível agora. Os botões continuam funcionando."
ESGOTOU = "Não consegui terminar. Peça ao Claude."
TIMEOUT = 180


def _post_json(url: str, payload: dict, timeout: float) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


class Chat:
    def __init__(self, url: str, modelo: str, keep_alive: str,
                 http: Callable[[str, dict, float], dict] = _post_json):
        self.url, self.modelo, self.keep_alive, self.http = url.rstrip("/"), modelo, keep_alive, http

    def responder(self, historico: list[dict], ferramentas: list[dict],
                  chamar: Callable[[str, dict], dict], max_rodadas: int = 5) -> dict:
        msgs = [{"role": "system", "content": SISTEMA}] + list(historico)
        propostas: list[str] = []
        for _ in range(max_rodadas):
            payload = {"model": self.modelo, "messages": msgs, "tools": ferramentas, "stream": False,
                       "keep_alive": self.keep_alive, "think": False}
            try:
                m = self.http(f"{self.url}/api/chat", payload, TIMEOUT)["message"]
            except (URLError, socket.timeout, TimeoutError, ConnectionError, KeyError, ValueError):
                return {"texto": INDISPONIVEL, "propostas": propostas}
            chamadas = m.get("tool_calls") or []
            if not chamadas:
                return {"texto": (m.get("content") or "").strip(), "propostas": propostas}
            msgs.append(m)
            for c in chamadas:
                f = c.get("function", {})
                args = f.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except ValueError:
                        args = {}
                res = chamar(f.get("name", ""), args)
                if isinstance(res, dict) and res.get("proposta"):
                    propostas.append(res["proposta"])
                msgs.append({"role": "tool", "content": json.dumps(res, ensure_ascii=False)})
        return {"texto": ESGOTOU, "propostas": propostas}


def aviso_gpu(ex: Executor) -> str | None:
    jogo = gpu.jogo_rodando(ex)
    if not jogo:
        return None
    return f"Tem um jogo aberto ({jogo}). Carregar o modelo pode deixar o jogo lento. Enviar mesmo assim?"
