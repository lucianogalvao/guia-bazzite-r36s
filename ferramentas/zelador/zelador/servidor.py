"""Servidor HTTP: página (web/) e API. Tudo em /api exige o cookie do PIN, menos /api/login."""
from __future__ import annotations

import json
import mimetypes
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
from .tarefas import Tarefas

mimetypes.add_type("application/manifest+json", ".webmanifest")


class App:
    def __init__(self, ex: Executor, estado: Path, web: Path, chat=None, esperar_sunshine: float = 3):
        self.ex, self.web = ex, Path(web).resolve()
        self.auth = Auth(estado)
        self.tarefas = Tarefas(Path(estado) / "tarefas")
        self.propostas = Propostas(Path(estado) / "propostas", self.tarefas)
        self.chat = chat or chat_mod.Chat(config.OLLAMA_URL, config.MODELO, config.KEEP_ALIVE)
        self.ferramentas, self.chamar = criar_registro(ex, self.propostas)
        self.acoes = dict(acoes.ACOES)
        self.acoes["reiniciar_sunshine"] = partial(acoes.reiniciar_sunshine, esperar=esperar_sunshine)


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

    def _logado(self) -> bool:
        c = SimpleCookie(self.headers.get("Cookie") or "")
        return self.app.auth.valida(c["zelador"].value if "zelador" in c else None)

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
            return self._json(200, {"itens": itens, "resumo": diagnostico.resumo(itens)})
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
        p = urlparse(self.path).path
        app, corpo = self.app, self._corpo()
        if p == "/api/login":
            try:
                ok = app.auth.conferir(str(corpo.get("pin", "")))
            except Bloqueado:
                return self._json(429, {"erro": "Muitas tentativas. Espere um minuto."})
            if not ok:
                return self._json(401, {"erro": "PIN errado."})
            t = app.auth.nova_sessao()
            return self._json(200, {"ok": True},
                              cookie=f"zelador={t}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000")
        if not self._logado():
            return self._json(401, {"erro": "Entre com o PIN."})
        if p.startswith("/api/acao/"):
            f = app.acoes.get(p.rsplit("/", 1)[-1])
            return self._json(200, f(app.ex)) if f else self._json(404, {"erro": "Ação não existe."})
        if p == "/api/chat":
            hist = [m for m in corpo.get("historico", []) if isinstance(m, dict)
                    and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)][-20:]
            aviso = chat_mod.aviso_gpu(app.ex)
            if aviso and not corpo.get("forcar"):
                return self._json(200, {"aviso": aviso})
            r = app.chat.responder(hist, app.ferramentas, app.chamar)
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
                   esperar_sunshine: float = 3) -> ThreadingHTTPServer:
    app = App(ex, estado, web, chat, esperar_sunshine)
    handler = type("H", (Handler,), {"app": app})
    srv = ThreadingHTTPServer(endereco, handler)
    srv.daemon_threads = True
    srv.app = app
    return srv
