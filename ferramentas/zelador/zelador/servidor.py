"""Servidor HTTP: página (web/) e API. Tudo em /api exige o cookie do PIN, menos /api/login."""
from __future__ import annotations

import ipaddress
import json
import mimetypes
import os
import socket
import threading
from functools import partial
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import acoes, chat as chat_mod, config, diagnostico
from .auth import Auth, Bloqueado
from .executor import Executor
from .ferramentas import criar_registro
from .propostas import Propostas
from .registro import Registro
from .tarefas import Tarefas

mimetypes.add_type("application/manifest+json", ".webmanifest")


class App:
    def __init__(self, ex: Executor, estado: Path, web: Path, chat=None, esperar_sunshine: float = 3,
                 desligar=acoes.desligar_pc):
        self.ex, self.web = ex, Path(web).resolve()
        self.nomes = _nomes_do_pc()
        self.auth = Auth(estado)
        self.registro = Registro(Path(estado) / "registro")
        self.tarefas = Tarefas(Path(estado) / "tarefas", ao_terminar=self._tarefa_terminou)
        self.propostas = Propostas(Path(estado) / "propostas", self.tarefas, registro=self.registro)
        self.chat = chat or chat_mod.Chat(config.OLLAMA_URL, config.MODELO, config.KEEP_ALIVE)
        self.ferramentas, chamar = criar_registro(ex, self.propostas)
        self._local = threading.local()  # ferramentas usadas, por requisição (cada uma tem sua thread)

        def chamar_anotando(nome: str, args: dict) -> dict:
            self._local.__dict__.setdefault("usadas", []).append(nome)
            return chamar(nome, args)
        self.chamar = chamar_anotando
        self.acoes = dict(acoes.ACOES)
        self.acoes["reiniciar_sunshine"] = partial(acoes.reiniciar_sunshine, esperar=esperar_sunshine)
        self.desligar = desligar


    def _tarefa_terminou(self, e: dict) -> None:
        sit = {"ok": "concluída", "falhou": "falhou"}.get(e["situacao"], e["situacao"])
        self.registro.anotar("tarefa", f"{e['titulo']}: {sit} ({e['passo']}/{e['total']})")


NOMES_ACAO = {"reiniciar_sunshine": "Reiniciar o streaming", "backup_agora": "Backup dos saves", "status": "Status"}


def _nomes_do_pc() -> set[str]:
    nome = socket.gethostname().lower().removesuffix(".local")
    extras = os.environ.get("ZELADOR_HOSTS", "")
    return {"localhost", nome, f"{nome}.local"} | {h.strip().lower() for h in extras.split(",") if h.strip()}


def host_permitido(host: str | None, nomes: set[str]) -> bool:
    """Contra DNS rebinding: só aceita IP direto ou o nome do próprio PC no cabeçalho Host."""
    if not host:
        return False
    host = host.strip().lower()
    if host.startswith("["):  # [IPv6]:porta
        nome = host[1:host.find("]")] if "]" in host else ""
    else:
        nome = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    try:
        ipaddress.ip_address(nome)
        return True
    except ValueError:
        return nome.rstrip(".") in nomes


class Handler(BaseHTTPRequestHandler):
    app: App
    server_version = "Zelador"

    def log_message(self, fmt, *args):  # silencioso; o journal já registra o serviço
        pass

    def _json(self, codigo: int, dados, cookie: str | None = None) -> None:
        corpo = json.dumps(dados, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            d = json.loads(self.rfile.read(min(n, 1_000_000)))
            return d if isinstance(d, dict) else {}
        except ValueError:
            return {}

    def _anotar(self, tipo: str, texto: str) -> None:
        self.app.registro.anotar(tipo, texto, origem=self.client_address[0])

    def _logado(self) -> bool:
        c = SimpleCookie(self.headers.get("Cookie") or "")
        return self.app.auth.valida(c["zelador"].value if "zelador" in c else None)

    def _host_ok(self) -> bool:
        if host_permitido(self.headers.get("Host"), self.app.nomes):
            return True
        self.send_error(403, "Host não permitido")
        return False

    def _estatico(self, caminho: str) -> None:
        rel = unquote(caminho).lstrip("/") or "index.html"
        alvo = (self.app.web / rel).resolve()
        if self.app.web not in alvo.parents or not alvo.is_file():
            self.send_error(404)
            return
        corpo = alvo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(alvo.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        if not self._host_ok():
            return
        p = urlparse(self.path).path
        if not p.startswith("/api/"):
            return self._estatico(p)
        if not self._logado():
            return self._json(401, {"erro": "Entre com o PIN."})
        app = self.app
        if p == "/api/status":
            return self._json(200, acoes.status(app.ex))
        if p == "/api/diagnostico":
            itens = diagnostico.regras(diagnostico.coletar(app.ex))
            self._anotar("diagnostico", diagnostico.resumo(itens))
            return self._json(200, {"itens": itens, "resumo": diagnostico.resumo(itens)})
        if p == "/api/registro":
            return self._json(200, app.registro.listar())
        if p == "/api/propostas":
            return self._json(200, app.propostas.pendentes())
        if p == "/api/tarefas":
            return self._json(200, app.tarefas.listar()[:20])
        if p.startswith("/api/tarefa/"):
            id_ = p.rsplit("/", 1)[-1]
            if not id_.replace("-", "").isalnum():
                return self._json(404, {"erro": "Tarefa não existe."})
            try:
                return self._json(200, app.tarefas.estado(id_))
            except OSError:
                return self._json(404, {"erro": "Tarefa não existe."})
        return self._json(404, {"erro": "Rota não existe."})

    def do_POST(self):
        if not self._host_ok():
            return
        p = urlparse(self.path).path
        app, corpo = self.app, self._corpo()
        if p == "/api/login":
            try:
                ok = app.auth.conferir(str(corpo.get("pin", "")), self.client_address[0])
            except Bloqueado as b:
                self._anotar("login", "Bloqueado: muitas tentativas")
                minutos = max(1, -(-b.segundos // 60))
                return self._json(429, {"erro": f"Muitas tentativas. Tente de novo em {minutos} min."})
            if not ok:
                self._anotar("login", "PIN errado")
                return self._json(401, {"erro": "PIN errado."})
            self._anotar("login", "Entrou")
            t = app.auth.nova_sessao()
            return self._json(200, {"ok": True},
                              cookie=f"zelador={t}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000")
        if not self._logado():
            return self._json(401, {"erro": "Entre com o PIN."})
        if p.startswith("/api/acao/"):
            nome = p.rsplit("/", 1)[-1]
            f = app.acoes.get(nome)
            if not f:
                return self._json(404, {"erro": "Ação não existe."})
            r = f(app.ex)
            resumo = r.get("mensagem") or ("Sunshine " + str(r.get("sunshine")) if nome == "status" else "feito")
            self._anotar("acao", f"{NOMES_ACAO.get(nome, nome)}: {resumo}")
            return self._json(200, r)
        if p == "/api/desligar":  # fora de /api/acao: exige confirmação explícita no corpo
            if corpo.get("confirmar") is not True:
                return self._json(400, {"erro": "Confirme para desligar."})
            r = app.desligar(app.ex)
            self._anotar("acao", f"Desligar o PC: {r['mensagem']}")
            return self._json(200, r)
        if p == "/api/chat":
            hist = [m for m in corpo.get("historico", []) if isinstance(m, dict)
                    and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)][-20:]
            aviso = chat_mod.aviso_gpu(app.ex)
            if aviso and not corpo.get("forcar"):
                return self._json(200, {"aviso": aviso})
            app._local.usadas = []
            r = app.chat.responder(hist, app.ferramentas, app.chamar)
            pergunta = next((m["content"] for m in reversed(hist) if m["role"] == "user"), "")
            us = app._local.usadas
            usadas = f" [ferramentas: {', '.join(dict.fromkeys(us))}]" if us else ""
            self._anotar("chat", f"Pergunta: {pergunta} → Resposta: {r.get('texto', '')}{usadas}")
            r["propostas"] = [x for x in app.propostas.pendentes() if x["id"] in r.get("propostas", [])]
            return self._json(200, r)
        if p == "/api/fechar_jogo":
            r = app.chamar("propor_fechar_jogo", {})
            if "erro" in r:
                return self._json(200, r)
            prop = next((x for x in app.propostas.pendentes() if x["id"] == r["proposta"]), None)
            return self._json(200, {"proposta": prop})
        if p.startswith("/api/aprovar/"):
            return self._json(200, app.propostas.aprovar(p.rsplit("/", 1)[-1], bool(corpo.get("confirmar_apagar"))))
        if p.startswith("/api/recusar/"):
            app.propostas.recusar(p.rsplit("/", 1)[-1])
            return self._json(200, {"ok": True})
        return self._json(404, {"erro": "Rota não existe."})


def criar_servidor(endereco, ex: Executor, estado: Path, web: Path, chat=None,
                   esperar_sunshine: float = 3, desligar=acoes.desligar_pc) -> ThreadingHTTPServer:
    app = App(ex, estado, web, chat, esperar_sunshine, desligar)
    handler = type("H", (Handler,), {"app": app})
    srv = ThreadingHTTPServer(endereco, handler)
    srv.daemon_threads = True
    srv.app = app
    return srv
