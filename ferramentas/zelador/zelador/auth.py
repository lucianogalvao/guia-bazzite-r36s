"""PIN simples e sessões por cookie. Proteção leve: só a rede de casa acessa."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path

MAX_ERROS = 5
BLOQUEIO_S = 60


class Bloqueado(Exception):
    pass


class Auth:
    def __init__(self, estado: Path):
        self.dir = Path(estado)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.arq_pin = self.dir / "pin"
        self.arq_sessoes = self.dir / "sessoes.json"
        self._erros, self._ate = 0, 0.0
        self._lock = threading.Lock()

    def _grava(self, arq: Path, texto: str) -> None:
        arq.write_text(texto)
        os.chmod(arq, 0o600)

    def definir_pin(self, pin: str) -> None:
        if not (pin.isdigit() and 4 <= len(pin) <= 6):
            raise ValueError("O PIN precisa ter de 4 a 6 números.")
        sal = secrets.token_hex(8)
        self._grava(self.arq_pin, f"{sal}:{hashlib.sha256((sal + pin).encode()).hexdigest()}")
        self._grava(self.arq_sessoes, "[]")

    def conferir(self, pin: str) -> bool:
        with self._lock:
            if time.time() < self._ate:
                raise Bloqueado()
            try:
                sal, h = self.arq_pin.read_text().strip().split(":")
            except (OSError, ValueError):
                return False
            ok = hmac.compare_digest(hashlib.sha256((sal + str(pin)).encode()).hexdigest(), h)
            if ok:
                self._erros = 0
            else:
                self._erros += 1
                if self._erros >= MAX_ERROS:
                    self._erros, self._ate = 0, time.time() + BLOQUEIO_S
            return ok

    def _sessoes(self) -> list[str]:
        try:
            return json.loads(self.arq_sessoes.read_text())
        except (OSError, ValueError):
            return []

    def nova_sessao(self) -> str:
        t = secrets.token_urlsafe(32)
        with self._lock:
            self._grava(self.arq_sessoes, json.dumps(self._sessoes()[-19:] + [t]))
        return t

    def valida(self, token: str | None) -> bool:
        return bool(token) and any(hmac.compare_digest(token, s) for s in self._sessoes())
