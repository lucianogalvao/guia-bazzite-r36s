"""Registro das ações (um arquivo por dia, JSON por linha). Guarda só os últimos 7 dias."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Callable

DIAS = 7
MAX_TEXTO = 300


class Registro:
    def __init__(self, dir: Path, dias: int = DIAS, agora: Callable[[], float] = time.time):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.dias, self.agora = dias, agora
        self._lock = threading.Lock()

    def _dia(self, t: float) -> str:
        return time.strftime("%Y-%m-%d", time.localtime(t))

    def _limpar(self, t: float) -> None:
        manter = {self._dia(t - i * 86400) for i in range(self.dias)}
        for f in self.dir.glob("*.jsonl"):
            if f.stem not in manter:
                f.unlink(missing_ok=True)

    def anotar(self, tipo: str, texto: str, origem: str | None = None) -> None:
        t = self.agora()
        texto = " ".join(str(texto).split())
        if len(texto) > MAX_TEXTO:
            texto = texto[: MAX_TEXTO - 1] + "…"
        item = {"t": t, "quando": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t)), "tipo": tipo, "texto": texto}
        if origem:
            item["origem"] = origem
        with self._lock:
            with (self.dir / f"{self._dia(t)}.jsonl").open("a") as f:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
            self._limpar(t)

    def listar(self, limite: int = 500) -> list[dict]:
        itens = []
        for f in sorted(self.dir.glob("*.jsonl"), reverse=True):
            for linha in reversed(f.read_text(errors="replace").splitlines()):
                try:
                    itens.append(json.loads(linha))
                except ValueError:
                    continue
                if len(itens) >= limite:
                    return itens
        return itens
