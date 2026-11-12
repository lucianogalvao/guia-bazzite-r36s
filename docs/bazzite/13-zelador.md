# 13 · Zelador: botões e chat no iPhone

## Objetivo

Resolver os problemas comuns do PC console pelo celular, do sofá, sem depender de outro computador: uma página servida pelo próprio PC, salva na tela de início do iPhone, com **botões** para as correções conhecidas e um **chat** com um modelo de linguagem rodando no PC.

- **Botões** (sem modelo, respondem na hora): Reiniciar Sunshine, "O que está acontecendo?", Status, Backup dos saves agora.
- **Chat** (modelo local `qwen3:8b` no Ollama): lê logs, explica erros, organiza `Downloads` e copia jogos para o cartão do R36S.
- **Tudo que mexe em arquivos vira uma proposta** com botão "Aprovar". Apagar pede uma segunda confirmação. O modelo não roda comandos livres: só as ferramentas de [`ferramentas/zelador/zelador/ferramentas.py`](../../ferramentas/zelador/zelador/ferramentas.py).
- Só funciona no **Wi-Fi de casa**. Com o PC desligado, a página não abre: ligue pela Alexa ou pelo Wake-on-LAN ([03](03-rede-wol.md)).

Os botões executam os mesmos comandos de [12 · Comandos do dia a dia](12-comandos.md), que continuam valendo à mão.

## Pré-requisitos

- Discos montados ([02](02-discos.md)), EmuDeck ([04](04-emudeck.md)) e Sunshine ([07](07-sunshine.md)).
- `loginctl enable-linger "$USER"` (já feito no [11](11-backup-saves.md)): os serviços rodam mesmo sem sessão aberta.
- Placa NVIDIA com o CDI do Podman (o Bazzite NVIDIA já vem assim). Confira com `nvidia-ctk cdi list`: deve listar `nvidia.com/gpu=all`.
- Uns 6 GB livres no NVMe para o modelo.

## Passos

1. **Copie o código** para o PC:

```bash
mkdir -p ~/.local/share/zelador
cp -r ferramentas/zelador/. ~/.local/share/zelador/      # ou rsync de outro computador
cd ~/.local/share/zelador && python3 -m unittest discover -s tests    # deve terminar em OK
```

2. **Ollama em contêiner, com a GPU** ([config/bazzite/ollama.container](../../config/bazzite/ollama.container)). Ele só escuta em `127.0.0.1` e guarda o modelo no NVMe:

```bash
mkdir -p /var/mnt/jogos/ollama ~/.config/containers/systemd
cp config/bazzite/ollama.container ~/.config/containers/systemd/
systemctl --user daemon-reload && systemctl --user start ollama
podman exec ollama ollama pull qwen3:8b
```

3. **Serviço do Zelador** ([config/bazzite/zelador.service](../../config/bazzite/zelador.service)) e o PIN (4 a 6 números):

```bash
cp config/bazzite/zelador.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now zelador
cd ~/.local/share/zelador && python3 -m zelador definir-pin
```

4. **No iPhone**, no Wi-Fi de casa: abra `http://IP-DO-PC:8787` no Safari → Compartilhar → **Adicionar à Tela de Início**. Entre com o PIN uma vez; ele fica lembrado.

**Atualizar:** copie de novo a pasta `ferramentas/zelador` e rode `systemctl --user restart zelador`.

**Testar fora do PC** (no Mac, por exemplo): `ZELADOR_FALSO=1 python3 -m zelador servir` sobe a página com dados de demonstração e PIN `0000`.

## Como usar

| Situação | O que fazer |
|---|---|
| Moonlight dá erro na TV | **Reiniciar Sunshine**. Se não resolver, **O que está acontecendo?** |
| Jogo ou emulador travado/aberto | Mais → **Fechar &lt;jogo&gt;** (ou peça no chat). Aprove na tela: o que não foi salvo se perde. Só fecha o que usa a placa de vídeo e não é Steam, Sunshine, ES-DE ou a área de trabalho |
| Baixou jogos | Avançado → **Organizar Downloads**. Confira o plano e aprove. Arquivos de torrent que ainda semeiam são **copiados**, não movidos |
| Quer pôr jogos no R36S | Cartão no leitor do PC → Avançado → **R36S**, depois peça no chat o que copiar |
| Pergunta qualquer | Chat. Se não for algo que ele sabe fazer, ele responde "Não sei fazer isso. Peça ao Claude." |

**Registro:** toda ação fica anotada, resumida, na seção "Registro dos últimos 7 dias" da página: entradas (com o IP do aparelho e PIN errado), botões, conversas (pergunta, resposta e ferramentas usadas), propostas (criada, aprovada, recusada ou barrada) e tarefas (concluída ou falhou). Os arquivos ficam em `~/.local/state/zelador/registro/AAAA-MM-DD.jsonl`, um por dia, e os com mais de 7 dias são apagados sozinhos. Pelo terminal:

```bash
tail -n 20 ~/.local/state/zelador/registro/$(date +%F).jsonl
```

O modelo ocupa a placa de vídeo enquanto responde e sai dela 5 minutos depois. Se houver um jogo aberto, o chat avisa antes de carregar.

## Verificação

```bash
systemctl --user is-active zelador ollama              # active / active
curl -s 127.0.0.1:11434/api/tags | grep qwen3          # modelo baixado
nvidia-smi | sed -n '/Processes/,$p'                   # ollama aparece só durante/logo após o chat
```

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| Respostas levam ~1 min; `podman exec ollama ollama ps` mostra `100% CPU` | O SELinux bloqueia a GPU no contêiner (`podman logs ollama` sem "library=CUDA"; `nvidia-smi` dentro dele dá "Insufficient Permissions") | `SecurityLabelDisable=true` no `ollama.container` (já está no arquivo do guia). Afrouxa o isolamento só desse contêiner, que escuta apenas em `127.0.0.1` |
| Primeira resposta demora ~1,5 min | O modelo está sendo carregado na placa de vídeo | Normal. As seguintes levam segundos; depois de 5 min parado ele sai da GPU e a próxima carrega de novo |
| `ollama ps` mostra parte na CPU (ex.: 14%/86%) | Pouca memória de vídeo livre (jogo/emulador ou Desktop abertos) | Normal: só fica um pouco mais lento |
| "O modelo está indisponível agora" | Ollama parado ou ainda carregando | `systemctl --user status ollama`. Os botões continuam funcionando |
| Página não abre no iPhone | Fora do Wi-Fi de casa, ou PC desligado | Conecte no Wi-Fi; ligue o PC pela Alexa/WoL |
| "Muitas tentativas" | 5 PINs errados seguidos | Espere 1 minuto |
| Esqueceu o PIN | — | `python3 -m zelador definir-pin` no PC (desconecta todos os aparelhos) |
| R36S: "ROOTFS do cartão está montada" | O PC montou a partição de sistema | Desmonte e reveja a regra udev do [r36s/01](../r36s/01-antes-de-tudo.md) |
