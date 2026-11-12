"""Tarefas longas em segundo plano, com log e estado em disco (sobrevivem ao cliente sair)."""
from __future__ import annotations

import json
import secrets
import subprocess
import threading
import time
from pathlib import Path


class Tarefas:
    def __init__(self, dir_logs: Path):
        self.dir = Path(dir_logs)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._vivas: set[str] = set()
        self._lock = threading.Lock()

    def _gravar(self, e: dict) -> None:
        tmp = self.dir / f"{e['id']}.json.tmp"
        tmp.write_text(json.dumps(e, ensure_ascii=False))
        tmp.replace(self.dir / f"{e['id']}.json")

    def iniciar(self, titulo: str, passos: list[list[str]]) -> str:
        id_ = time.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)
        e = {"id": id_, "titulo": titulo, "passo": 0, "total": len(passos), "situacao": "rodando",
             "criada": time.time()}
        self._gravar(e)
        with self._lock:
            self._vivas.add(id_)
        threading.Thread(target=self._rodar, args=(e, passos), daemon=True).start()
        return id_

    def _rodar(self, e: dict, passos: list[list[str]]) -> None:
        log = self.dir / f"{e['id']}.log"
        try:
            with log.open("a") as f:
                for i, args in enumerate(passos, 1):
                    f.write(f"== {' '.join(args)}\n")
                    f.flush()
                    try:
                        codigo = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT).returncode
                    except FileNotFoundError:
                        f.write(f"comando não encontrado: {args[0]}\n")
                        codigo = 127
                    if codigo != 0:
                        f.write(f"== falhou (código {codigo})\n")
                        e["situacao"] = "falhou"
                        break
                    e["passo"] = i
                    self._gravar(e)
                else:
                    e["situacao"] = "ok"
            self._gravar(e)
        finally:
            with self._lock:
                self._vivas.discard(e["id"])

    def estado(self, id_: str) -> dict:
        e = json.loads((self.dir / f"{id_}.json").read_text())
        with self._lock:
            viva = id_ in self._vivas
        if e["situacao"] == "rodando" and not viva:
            e["situacao"] = "interrompida"
        log = self.dir / f"{id_}.log"
        e["log_fim"] = "\n".join(log.read_text(errors="replace").splitlines()[-20:]) if log.exists() else ""
        return e

    def listar(self) -> list[dict]:
        ids = [p.name[: -len(".json")] for p in self.dir.glob("*.json")]
        es = [self.estado(i) for i in ids]
        return sorted(es, key=lambda e: e.get("criada", 0), reverse=True)
