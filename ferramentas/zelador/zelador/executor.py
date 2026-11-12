"""Execução de comandos do sistema, sempre como lista de argumentos (nunca shell)."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass
class Resultado:
    codigo: int
    saida: str
    erro: str


class Executor:
    def rodar(self, args: list[str], timeout: float = 30) -> Resultado:
        try:
            p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return Resultado(124, "", "timeout")
        except FileNotFoundError:
            return Resultado(127, "", f"comando não encontrado: {args[0]}")
        return Resultado(p.returncode, p.stdout, p.stderr)


@dataclass
class ExecutorFalso(Executor):
    """Responde pelo prefixo mais longo cadastrado em `respostas`. Para testes."""

    respostas: dict = field(default_factory=dict)
    chamadas: list = field(default_factory=list)

    def rodar(self, args: list[str], timeout: float = 30) -> Resultado:
        self.chamadas.append(list(args))
        melhor = None
        for chave in self.respostas:
            if tuple(args[: len(chave)]) == chave and (melhor is None or len(chave) > len(melhor)):
                melhor = chave
        if melhor is None:
            return Resultado(127, "", "sem resposta")
        return self.respostas[melhor]
