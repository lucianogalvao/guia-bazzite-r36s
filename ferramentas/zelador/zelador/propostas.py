"""Propostas: planos que mudam arquivos e só rodam depois de 'Aprovar' na página.

Ao aprovar, a proposta é refeita com a situação atual (cartão, torrents). Se mudou, é recusada.
"""
from __future__ import annotations

import json
import secrets
import threading
import time
from pathlib import Path
from typing import Callable

from .tarefas import Tarefas

NAO_EXISTE = "Proposta não existe ou já foi aprovada."
VALIDADE_S = 3600


class Propostas:
    def __init__(self, dir: Path, tarefas: Tarefas,
                 refazedores: dict[str, Callable[[dict], list[dict]]] | None = None, registro=None):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tarefas = tarefas
        self.refazedores = dict(refazedores or {})
        self.registro = registro
        self._lock = threading.Lock()

    def _anotar(self, texto: str) -> None:
        if self.registro:
            self.registro.anotar("proposta", texto)

    def _arq(self, id_: str) -> Path:
        return self.dir / f"{id_}.json"

    def criar(self, titulo: str, passos: list[dict], refazer: str | None = None, entrada=None) -> str:
        id_ = secrets.token_hex(4)
        p = {"id": id_, "titulo": titulo, "passos": passos, "criada": time.time(),
             "refazer": refazer, "entrada": entrada}
        tmp = self.dir / f"{id_}.tmp"
        tmp.write_text(json.dumps(p, ensure_ascii=False))
        tmp.replace(self._arq(id_))
        self._anotar(f"Criada: {titulo} ({len(passos)} passo(s))")
        return id_

    def pendentes(self) -> list[dict]:
        ps = []
        for f in self.dir.glob("*.json"):
            try:
                p = json.loads(f.read_text())
            except (OSError, ValueError):
                continue
            if time.time() - p.get("criada", 0) <= VALIDADE_S:
                ps.append(p)
        return sorted(ps, key=lambda p: p["criada"])

    def aprovar(self, id_: str, confirmar_apagar: bool = False) -> dict:
        if not id_.isalnum():
            return {"ok": False, "mensagem": NAO_EXISTE}
        with self._lock:
            arq = self._arq(id_)
            try:
                p = json.loads(arq.read_text())
            except (OSError, ValueError):
                return {"ok": False, "mensagem": NAO_EXISTE}
            if time.time() - p.get("criada", 0) > VALIDADE_S:
                arq.unlink(missing_ok=True)
                return {"ok": False, "mensagem": "A proposta expirou. Peça de novo."}
            if any(x.get("apaga") for x in p["passos"]) and not confirmar_apagar:
                return {"ok": False, "precisa_confirmar_apagar": True}
            if p.get("refazer"):
                try:
                    novos = self.refazedores[p["refazer"]](p.get("entrada"))
                except (ValueError, KeyError) as e:
                    arq.unlink(missing_ok=True)
                    self._anotar(f"Barrada: {p['titulo']}: {e}")
                    return {"ok": False, "mensagem": str(e)}
                if novos != p["passos"]:
                    arq.unlink(missing_ok=True)
                    self._anotar(f"Barrada (a situação mudou): {p['titulo']}")
                    return {"ok": False, "mensagem": "A situação mudou desde a proposta. Peça de novo."}
            arq.unlink()
        tarefa = self.tarefas.iniciar(p["titulo"], [x["args"] for x in p["passos"]])
        self._anotar(f"Aprovada: {p['titulo']}: " + "; ".join(x["descricao"] for x in p["passos"]))
        return {"ok": True, "tarefa": tarefa}

    def recusar(self, id_: str) -> None:
        if id_.isalnum():
            with self._lock:
                arq = self._arq(id_)
                try:
                    titulo = json.loads(arq.read_text())["titulo"]
                except (OSError, ValueError, KeyError):
                    return
                arq.unlink(missing_ok=True)
            self._anotar(f"Recusada: {titulo}")
