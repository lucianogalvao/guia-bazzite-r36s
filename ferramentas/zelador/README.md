# Zelador

Página com botões e chat para cuidar do PC console pelo iPhone. Instalação e uso: [docs/bazzite/13-zelador.md](../../docs/bazzite/13-zelador.md).

Só biblioteca padrão do Python (≥ 3.10). Sem `pip`.

```bash
python3 -m unittest discover -s tests -v          # testes (rodam em qualquer máquina)
ZELADOR_FALSO=1 python3 -m zelador servir         # demonstração, PIN 000000, porta 8787
python3 -m zelador definir-pin                    # trocar o PIN
```

| Módulo | Papel |
|---|---|
| `executor.py` | Roda comandos como lista de argumentos (nunca shell); `ExecutorFalso` para testes |
| `acoes.py` | Botões: status, reiniciar Sunshine, backup |
| `diagnostico.py` | "O que está acontecendo?" por regras, sem modelo |
| `gpu.py` | Há jogo usando a placa de vídeo? |
| `roms.py` | Downloads, torrents ativos (lê o `.fastresume` do qBittorrent), plano de organização |
| `r36s.py` | Cartão do R36S: só `EASYROMS`, nunca monta o `ROOTFS` |
| `propostas.py` | Planos que mudam arquivos; só rodam após "Aprovar" |
| `tarefas.py` | Execução em segundo plano com log em `~/.local/state/zelador/tarefas` |
| `registro.py` | Registro das ações, um `.jsonl` por dia, guarda 7 dias |
| `ferramentas.py` | A lista fechada do que o modelo pode fazer |
| `chat.py` | Conversa com o Ollama |
| `auth.py` / `servidor.py` | PIN, cookie e rotas HTTP |

Variáveis `ZELADOR_<NOME>` trocam os caminhos e constantes de `config.py` (porta, modelo, pastas).
