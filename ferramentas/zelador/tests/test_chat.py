import unittest
from urllib.error import URLError

from zelador import chat
from zelador.executor import ExecutorFalso, Resultado


class HttpFalso:
    def __init__(self, respostas):
        self.respostas, self.pedidos = list(respostas), []

    def __call__(self, url, payload, timeout):
        self.pedidos.append((url, payload))
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def msg(texto="", tool_calls=None):
    m = {"role": "assistant", "content": texto}
    if tool_calls:
        m["tool_calls"] = tool_calls
    return {"message": m}


def novo(http):
    return chat.Chat("http://ollama", "qwen3:8b", "5m", http=http)


class TestChat(unittest.TestCase):
    def test_resposta_simples(self):
        http = HttpFalso([msg("Oi!")])
        r = novo(http).responder([{"role": "user", "content": "oi"}], [], lambda n, a: {})
        self.assertEqual(r, {"texto": "Oi!", "propostas": []})
        url, payload = http.pedidos[0]
        self.assertEqual(url, "http://ollama/api/chat")
        self.assertEqual(payload["model"], "qwen3:8b")
        self.assertEqual(payload["keep_alive"], "5m")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["messages"][0], {"role": "system", "content": chat.SISTEMA})

    def test_laco_de_ferramenta(self):
        chamadas = []

        def chamar(nome, args):
            chamadas.append((nome, args))
            return {"proposta": "p1", "passos": ["x"]} if nome == "propor_organizacao" else {"sunshine": "active"}

        http = HttpFalso([
            msg(tool_calls=[{"function": {"name": "status", "arguments": {}}}]),
            msg(tool_calls=[{"function": {"name": "propor_organizacao", "arguments": {"itens": []}}}]),
            msg("Pronto, aprove na tela."),
        ])
        r = novo(http).responder([{"role": "user", "content": "organiza"}], [], chamar)
        self.assertEqual(chamadas, [("status", {}), ("propor_organizacao", {"itens": []})])
        self.assertEqual(r, {"texto": "Pronto, aprove na tela.", "propostas": ["p1"]})
        self.assertEqual(http.pedidos[1][1]["messages"][-1]["role"], "tool")

    def test_ollama_fora_do_ar(self):
        r = novo(HttpFalso([URLError("connection refused")])).responder([], [], lambda n, a: {})
        self.assertEqual(r["texto"], "O modelo está indisponível agora. Os botões continuam funcionando.")

    def test_mensagem_malformada_vira_indisponivel(self):
        r = novo(HttpFalso([{"message": "texto solto"}])).responder([], [], lambda n, a: {})
        self.assertEqual(r["texto"], chat.INDISPONIVEL)

    def test_tempo_total_limitado(self):
        loop = msg(tool_calls=[{"function": {"name": "status", "arguments": {}}}])
        c = novo(HttpFalso([loop] * 5))
        c.limite_total = 0
        self.assertEqual(c.responder([], [], lambda n, a: {})["texto"], chat.ESGOTOU)

    def test_limite_de_rodadas(self):
        loop = msg(tool_calls=[{"function": {"name": "status", "arguments": {}}}])
        r = novo(HttpFalso([loop] * 3)).responder([], [], lambda n, a: {}, max_rodadas=3)
        self.assertEqual(r["texto"], "Não consegui terminar. Peça ao Claude.")

    def test_sistema_proibe_dizer_aprovado(self):
        self.assertIn("Nunca diga que algo foi aprovado ou feito", chat.SISTEMA)

    def test_aviso_gpu_com_jogo(self):
        tabela = "|    0   N/A  N/A   26589    C+G   ...bin/eden        746MiB |\n"
        ex = ExecutorFalso({("nvidia-smi",): Resultado(0, tabela, "")})
        self.assertEqual(chat.aviso_gpu(ex),
                         "Tem um jogo aberto (eden). Carregar o modelo pode deixar o jogo lento. Enviar mesmo assim?")
        self.assertIsNone(chat.aviso_gpu(ExecutorFalso({("nvidia-smi",): Resultado(0, "", "")})))


if __name__ == "__main__":
    unittest.main()
