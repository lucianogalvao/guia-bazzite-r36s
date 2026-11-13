import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from urllib.error import HTTPError

from zelador import servidor
from zelador.auth import Auth
from zelador.executor import ExecutorFalso, Resultado


class ChatFalso:
    def responder(self, historico, ferramentas, chamar, max_rodadas=5):
        return {"texto": "ok", "propostas": []}


class TestServidor(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        web = self.dir / "web"
        web.mkdir()
        (web / "index.html").write_text("<h1>Zelador</h1>")
        (self.dir / "segredo.txt").write_text("não")
        self.ex = ExecutorFalso({
            ("systemctl", "--user", "restart"): Resultado(0, "", ""),
            ("systemctl", "--user", "is-active"): Resultado(0, "active\n", ""),
            ("nvidia-smi",): Resultado(0, "", ""),
        })
        Auth(self.dir / "estado").definir_pin("123456")
        self.srv = servidor.criar_servidor(("127.0.0.1", 0), self.ex, self.dir / "estado", web,
                                           chat=ChatFalso(), esperar_sunshine=0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.addCleanup(self.srv.server_close)
        self.addCleanup(self.srv.shutdown)
        self.base = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.cookie = None

    def req(self, metodo, caminho, corpo=None, host=None):
        r = urllib.request.Request(self.base + caminho, method=metodo,
                                   data=None if corpo is None else json.dumps(corpo).encode())
        if host:
            r.add_header("Host", host)
        if self.cookie:
            r.add_header("Cookie", self.cookie)
        try:
            with urllib.request.urlopen(r) as resp:
                ck = resp.headers.get("Set-Cookie")
                if ck:
                    self.cookie = ck.split(";")[0]
                return resp.status, resp.read()
        except HTTPError as e:
            return e.code, e.read()

    def login(self, pin="123456"):
        return self.req("POST", "/api/login", {"pin": pin})

    def test_pagina_sem_login(self):
        st, corpo = self.req("GET", "/")
        self.assertEqual((st, corpo), (200, b"<h1>Zelador</h1>"))

    def test_api_sem_cookie_401(self):
        self.assertEqual(self.req("GET", "/api/status")[0], 401)
        self.assertEqual(self.req("POST", "/api/acao/reiniciar_sunshine")[0], 401)

    def test_login_errado_401_e_bloqueio(self):
        for _ in range(5):
            self.assertEqual(self.login("000000")[0], 401)
        st, corpo = self.login("123456")
        self.assertEqual(st, 429)
        self.assertIn("Muitas tentativas", json.loads(corpo)["erro"])

    def test_login_e_reiniciar_sunshine(self):
        self.assertEqual(self.login()[0], 200)
        st, corpo = self.req("POST", "/api/acao/reiniciar_sunshine")
        self.assertEqual(st, 200)
        self.assertEqual(json.loads(corpo)["mensagem"], "Sunshine reiniciado e rodando.")
        self.assertEqual(self.req("POST", "/api/acao/apagar_tudo")[0], 404)

    def test_recusa_host_de_outro_dominio(self):
        porta = self.srv.server_address[1]
        for host in (f"ataque.example:{porta}", "ataque.example", f"127.0.0.1.nip.io:{porta}"):
            self.assertEqual(self.req("POST", "/api/login", {"pin": "123456"}, host=host)[0], 403, host)
            self.assertEqual(self.req("GET", "/", host=host)[0], 403, host)
        self.assertIsNone(self.cookie)

    def test_aceita_ip_e_nome_do_pc(self):
        porta = self.srv.server_address[1]
        for host in (f"192.168.0.10:{porta}", "192.168.0.10", f"[::1]:{porta}", f"localhost:{porta}",
                     f"{socket.gethostname()}:{porta}", f"{socket.gethostname()}.local:{porta}"):
            self.assertEqual(self.req("GET", "/", host=host)[0], 200, host)

    def test_pastas_de_estado_so_do_dono(self):
        estado = self.dir / "estado"
        for d in (estado, estado / "registro", estado / "propostas", estado / "tarefas"):
            self.assertEqual(d.stat().st_mode & 0o777, 0o700, d)

    def test_web_bloqueia_ponto_ponto(self):
        self.assertEqual(self.req("GET", "/../segredo.txt")[0], 404)
        self.assertEqual(self.req("GET", "/%2e%2e/segredo.txt")[0], 404)

    def test_tarefas_lista_em_andamento(self):
        self.login()
        app = self.srv.app
        id_ = app.propostas.criar("lenta", [{"descricao": "d", "args": ["sleep", "0.5"], "apaga": False}])
        st, corpo = self.req("POST", f"/api/aprovar/{id_}", {})
        self.assertEqual(st, 200)
        tarefa = json.loads(corpo)["tarefa"]
        ids = [t["id"] for t in json.loads(self.req("GET", "/api/tarefas")[1])]
        self.assertIn(tarefa, ids)

    def test_rota_fechar_jogo_cria_proposta(self):
        self.login()
        self.ex.respostas[("nvidia-smi",)] = Resultado(0, "|    0   N/A  N/A   26589    C+G   /x/bin/eden   746MiB |\n", "")
        st, corpo = self.req("POST", "/api/fechar_jogo", {})
        d = json.loads(corpo)
        self.assertEqual(st, 200)
        self.assertEqual(d["proposta"]["passos"][0]["args"], ["kill", "-TERM", "26589"])

    def test_rota_fechar_jogo_sem_jogo(self):
        self.login()
        st, corpo = self.req("POST", "/api/fechar_jogo", {})
        self.assertEqual(json.loads(corpo), {"erro": "Nenhum jogo aberto."})

    def registro(self):
        return json.loads(self.req("GET", "/api/registro")[1])

    def test_registro_exige_login(self):
        self.assertEqual(self.req("GET", "/api/registro")[0], 401)

    def test_registro_de_login_errado_e_acao(self):
        self.login("999999")
        self.login()
        self.req("POST", "/api/acao/reiniciar_sunshine")
        itens = self.registro()
        tipos = [i["tipo"] for i in itens]
        self.assertEqual(tipos[:3], ["acao", "login", "login"])
        self.assertIn("Sunshine reiniciado", itens[0]["texto"])
        self.assertIn("PIN errado", itens[2]["texto"])
        self.assertEqual(itens[0]["origem"], "127.0.0.1")

    def test_registro_de_chat_e_proposta(self):
        self.login()
        self.req("POST", "/api/chat", {"historico": [{"role": "user", "content": "como está o PC?"}], "forcar": True})
        id_ = self.srv.app.propostas.criar("Organizar Downloads", [{"descricao": "d", "args": ["true"], "apaga": False}])
        self.req("POST", f"/api/aprovar/{id_}", {})
        textos = " | ".join(i["texto"] for i in self.registro())
        self.assertIn("como está o PC?", textos)
        self.assertIn("Aprovada: Organizar Downloads", textos)

    def test_registro_de_tarefa_concluida(self):
        self.login()
        id_ = self.srv.app.propostas.criar("Rápida", [{"descricao": "d", "args": ["true"], "apaga": False}])
        self.req("POST", f"/api/aprovar/{id_}", {})
        fim = time.time() + 5
        while time.time() < fim and not any(i["tipo"] == "tarefa" for i in self.registro()):
            time.sleep(0.05)
        t = [i for i in self.registro() if i["tipo"] == "tarefa"][0]
        self.assertIn("Rápida", t["texto"])
        self.assertIn("concluída", t["texto"])

    def test_chat_avisa_com_jogo(self):
        self.login()
        self.ex.respostas[("nvidia-smi",)] = Resultado(0, "|    0   N/A  N/A   1    G   /x/eden   900MiB |\n", "")
        st, corpo = self.req("POST", "/api/chat", {"historico": [{"role": "user", "content": "oi"}]})
        self.assertIn("aviso", json.loads(corpo))
        st, corpo = self.req("POST", "/api/chat", {"historico": [{"role": "user", "content": "oi"}], "forcar": True})
        self.assertEqual(json.loads(corpo)["texto"], "ok")


if __name__ == "__main__":
    unittest.main()
