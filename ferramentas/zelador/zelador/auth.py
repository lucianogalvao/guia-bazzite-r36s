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

LIVRES = 5           # erros seguidos antes do primeiro bloqueio
BLOQUEIO_S = 60      # primeiro bloqueio; dobra a cada erro seguinte
BLOQUEIO_MAX_S = 3600


class Bloqueado(Exception):
    def __init__(self, segundos: int):
        super().__init__(segundos)
        self.segundos = segundos


class Auth:
    def __init__(self, estado: Path, relogio=time.time):
        self.dir = Path(estado)
        self.dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.dir, 0o700)  # registro e propostas guardam conversas
        self.arq_pin = self.dir / "pin"
        self.arq_sessoes = self.dir / "sessoes.json"
        self._relogio = relogio
        self._erros: dict[str, list] = {}  # ip -> [erros seguidos, bloqueado até]
        self._lock = threading.Lock()

    def _grava(self, arq: Path, texto: str) -> None:
        arq.write_text(texto)
        os.chmod(arq, 0o600)

    def definir_pin(self, pin: str) -> None:
        if not (pin.isdigit() and len(pin) == 6):
            raise ValueError("O PIN precisa ter 6 números.")
        sal = secrets.token_hex(8)
        self._grava(self.arq_pin, f"{sal}:{hashlib.sha256((sal + pin).encode()).hexdigest()}")
        self._grava(self.arq_sessoes, "[]")

    def conferir(self, pin: str, ip: str = "") -> bool:
        """Bloqueio por aparelho: um aparelho errando não tranca os outros."""
        with self._lock:
            agora = self._relogio()
            erros, ate = self._erros.get(ip, (0, 0.0))
            if agora < ate:
                raise Bloqueado(round(ate - agora))
            try:
                sal, h = self.arq_pin.read_text().strip().split(":")
            except (OSError, ValueError):
                return False
            ok = hmac.compare_digest(hashlib.sha256((sal + str(pin)).encode()).hexdigest(), h)
            if ok:
                self._erros.pop(ip, None)
                return True
            erros += 1
            espera = min(BLOQUEIO_S * 2 ** (erros - LIVRES), BLOQUEIO_MAX_S) if erros >= LIVRES else 0
            if len(self._erros) > 1000:  # não deixa a tabela crescer sem fim
                self._erros = {k: v for k, v in self._erros.items() if v[1] > agora}
            self._erros[ip] = [erros, agora + espera]
            return False

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
