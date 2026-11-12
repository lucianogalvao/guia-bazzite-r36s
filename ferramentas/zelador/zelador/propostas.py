"""Propostas: planos que mudam arquivos e só rodam depois de 'Aprovar' na página."""
from __future__ import annotations

import json
import secrets
import threading
import time
from pathlib import Path

from .tarefas import Tarefas

NAO_EXISTE = "Proposta não existe ou já foi aprovada."


class Propostas:
    def __init__(self, dir: Path, tarefas: Tarefas):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tarefas = tarefas
        self._lock = threading.Lock()

    def _arq(self, id_: str) -> Path:
        return self.dir / f"{id_}.json"

    def criar(self, titulo: str, passos: list[dict]) -> str:
        id_ = secrets.token_hex(4)
        p = {"id": id_, "titulo": titulo, "passos": passos, "criada": time.time()}
        self._arq(id_).write_text(json.dumps(p, ensure_ascii=False))
        return id_

    def pendentes(self) -> list[dict]:
        ps = [json.loads(f.read_text()) for f in self.dir.glob("*.json")]
        return sorted(ps, key=lambda p: p["criada"])

    def aprovar(self, id_: str, confirmar_apagar: bool = False) -> dict:
        if not id_.isalnum():
            return {"ok": False, "mensagem": NAO_EXISTE}
        with self._lock:
            arq = self._arq(id_)
            if not arq.exists():
                return {"ok": False, "mensagem": NAO_EXISTE}
            p = json.loads(arq.read_text())
            if any(x.get("apaga") for x in p["passos"]) and not confirmar_apagar:
                return {"ok": False, "precisa_confirmar_apagar": True}
            arq.unlink()
        tarefa = self.tarefas.iniciar(p["titulo"], [x["args"] for x in p["passos"]])
        return {"ok": True, "tarefa": tarefa}

    def recusar(self, id_: str) -> None:
        if id_.isalnum():
            with self._lock:
                self._arq(id_).unlink(missing_ok=True)
