# Zelador: agente local do PC console, acessado pelo iPhone

Data: 2026-11-12 · Estado: rascunho para aprovação

## Intenção

O PC console (Bazzite, sala de casa) às vezes dá problema e, hoje, quem resolve é o Claude no Mac. Quando a cota do Claude acaba, ou quando ninguém está no Mac, o problema fica parado. Exemplo real: o Moonlight dá erro na TV e a solução era reiniciar o Sunshine.

O Zelador é um **plano B local**: uma página no próprio PC, salva na tela de início do iPhone, com **botões** para as correções conhecidas e um **chat** com um modelo de linguagem rodando no PC, para ler logs, explicar erros, rodar os scripts do guia e organizar ROMs (no PC e no cartão do R36S).

Não substitui o Claude. É menos inteligente, e por isso deve **avisar quando não souber**, em vez de inventar.

## Quem usa

- O dono (técnico, usa SSH, conhece o guia).
- A esposa (não técnica). A tela principal precisa funcionar para ela sem explicação.

Os dois, pelo iPhone, no **Wi-Fi de casa**, normalmente do sofá, com a TV na frente.

## Objetivos

1. **Botões para ações conhecidas**, que respondem na hora e funcionam mesmo com o modelo fora do ar. O primeiro e mais importante: **Reiniciar Sunshine**.
2. **"O que está acontecendo?"**: um diagnóstico em português, a partir do estado dos serviços e dos logs (Sunshine, journal), com a correção sugerida. Se a correção for um dos botões, ele oferece o botão.
3. **Chat** com o modelo local para pedidos abertos: ler logs, rodar scripts do guia, organizar `Downloads`.
4. **Organizar ROMs** de `/var/mnt/roms/Downloads` seguindo as regras já definidas no guia e no prompt do agente (`~/Desktop/prompt-agente-roms.md`): identificar, mostrar o plano, esperar a aprovação, extrair/converter, verificar e mover.
5. **R36S:** com o cartão no leitor USB do PC, copiar ROMs, saves e BIOS/firmware para a partição `EASYROMS`.

## Não objetivos

- Acesso fora de casa (sem 4G, sem Tailscale, sem túnel).
- App nativo, App Store, notificações push.
- Ligar o PC: com o PC desligado, a página não existe. Para isso continuam a Alexa e o Wake-on-LAN ([03](../../bazzite/03-rede-wol.md)).
- Substituir o Claude em tarefas novas ou complexas.
- Baixar ROMs, BIOS ou firmware da internet.

## Antiobjetivos (falhou, mesmo que funcione)

- **Atrapalhar um jogo**: deixar um jogo lento ou sem memória de vídeo por causa do modelo.
- **Estragar o cartão do R36S**: montar ou escrever no `ROOTFS` (btrfs) do cartão. Ver [r36s/01](../../r36s/01-antes-de-tudo.md): só montar já quebra o boot.
- **Perder arquivos**: apagar ou sobrescrever sem confirmação explícita na tela.
- **Quebrar o seed** do qBittorrent: apagar ou mover arquivos de torrents ativos.
- **Inventar**: o modelo afirmar que corrigiu algo que não corrigiu, ou dar um diagnóstico sem ter lido nada.
- **Depender de serviço externo** para funcionar (nuvem, Discord, conta).
- **Ser complicado para a esposa**: precisar ler texto técnico para resolver o caso comum.

## Restrições

| Item | Valor |
|---|---|
| Sistema | Bazzite 45 (Fedora Atomic/Kinoite), imutável. Nada de `rpm-ostree` ou `dnf`. Instalar em `~`, Homebrew (`/home/linuxbrew`), Flatpak ou Podman |
| Hardware | i5-10400F, 32 GB RAM, RTX 3060 Ti **8 GB** (driver 620). Uns 1,6 GB de VRAM já ficam ocupados pela sessão |
| Disponível | `podman`, `python3` 3.15, Homebrew. Ollama **não** está instalado |
| Rede | Só LAN. O IP do PC é fixo ([03](../../bazzite/03-rede-wol.md)) |
| Portas em uso | Sunshine (47990 e as do Moonlight) |
| Serviços | Tudo como serviço **de usuário** do systemd, com `linger` (já ativo), como o `backup-saves` |
| Usuários | iPhone (Safari, "Adicionar à Tela de Início") |

## Decisões tomadas

As decisões do dono estão marcadas como **(dono)**. As que eu tomei estão marcadas como **(Claude)**, e o dono pode revisar.

1. **Interface: PWA servida pelo próprio PC** (dono). Uma página, salva na tela de início do iPhone. Sem app e sem serviço externo.
2. **Só no Wi-Fi de casa** (dono).
3. **Duas camadas** (dono confirmou): botões com comandos fixos e chat com o modelo.
4. **R36S pelo leitor USB do PC** (dono). O cartão fica no leitor e o agente automatiza a cópia.
5. **Só é usado fora do jogo** (dono). Mesmo assim, a política de VRAM do item 9 vale.
6. **Stack** (dono deixou para o Claude):
   - Ollama rodando o modelo, num contêiner Podman com GPU NVIDIA, ou outra forma que funcione no Bazzite sem mexer no sistema.
   - Modelo de 7 a 8 B com bom suporte a chamada de ferramentas (*tool calling*), quantizado para caber em uns 6 GB, contexto modesto.
   - Servidor pequeno em Python servindo a página, os botões e o chat.
   - Código neste repositório (o guia), em `ferramentas/zelador/`, com serviço em `config/bazzite/` e capítulo novo em `docs/bazzite/`.
7. **O modelo não roda shell livre** (Claude). Ele só chama **ferramentas de uma lista fixa**, como ler log, ver status, rodar script do guia ou listar downloads. Modelos pequenos erram comandos, e uma lista fixa limita o estrago. Para algo fora da lista, ele responde "não sei fazer isso, chame o Claude".
8. **Confirmação na tela para tudo que muda arquivos** (Claude): mover, extrair, apagar, copiar para o R36S. O modelo propõe um plano e um botão "Aprovar" executa. Apagar exige confirmação separada.
9. **VRAM sob demanda** (Claude): o modelo é carregado só quando o chat é usado e descarregado depois de cerca de 5 minutos parado. Se um jogo estiver rodando, o chat avisa antes de carregar. Os botões nunca usam o modelo.
10. **PIN simples** (Claude): um PIN de 4 a 6 dígitos na primeira abertura, lembrado no aparelho. Proteção leve, já que só a rede de casa acessa.
11. **Regras de ROMs = as do prompt do agente** (Claude). Não se cria um segundo conjunto de regras: o `CLAUDE.md`/prompt das ROMs é a fonte.
12. **Regras do R36S** (Claude): só a partição `EASYROMS` (exFAT, montada pelo sistema normalmente). Se o `ROOTFS` aparecer montado, o agente para e avisa. Ele nunca chama `mount` em btrfs do cartão.

13. **Sem `sudo`** (Claude): o Zelador roda como o usuário e nunca pede senha de administrador. O que exigir root (fstab, udev, `/etc`) fica fora, com a resposta "isso precisa ser feito à mão; veja o guia".
14. **Tarefas longas em segundo plano** (Claude): extrair ou copiar dezenas de GB vira uma tarefa com log, como em [12](../../bazzite/12-comandos.md). A página mostra o progresso e a tarefa continua se o iPhone travar ou fechar a página.
15. **Modelo no NVMe** (Claude): os arquivos do modelo ficam em `/var/mnt/jogos`, não no SSD do sistema.
16. **Comandos dos botões = os do guia** (Claude): cada botão executa exatamente o que está documentado em [12 · Comandos do dia a dia](../../bazzite/12-comandos.md), para que tudo possa ser feito à mão, e o documento e o código não divirjam.

## Botões iniciais (Claude, para revisar)

| Botão | O que faz | Quem usa |
|---|---|---|
| **Reiniciar Sunshine** | `systemctl --user restart app-dev.lizardbyte.app.Sunshine`, espera e confere que voltou | Os dois |
| **O que está acontecendo?** | Coleta status e logs recentes e pede um diagnóstico ao modelo. Se o modelo não estiver disponível, mostra o resumo bruto | Os dois |
| **Status** | PC, Sunshine, jogo rodando ou não, discos montados, último backup dos saves, espaço livre | Dono |
| **Backup dos saves agora** | `systemctl --user start backup-saves.service` | Dono |
| **Organizar Downloads** | Abre o chat já com o pedido, e o plano aparece para aprovar | Dono |
| **R36S** | Detecta o cartão, mostra o espaço e as opções de cópia | Dono |

Os dois primeiros ficam grandes, no topo. O resto fica abaixo ou numa área "Avançado".

## O que fica com quem constrói

- Qual modelo exatamente, e como rodar o Ollama com GPU no Bazzite (testar Podman + CDI da NVIDIA).
- Framework web (biblioteca padrão ou algo leve num venv em `~`), formato do PWA (manifest, ícone), porta.
- Lista exata de ferramentas do modelo e o formato das chamadas.
- Como detectar "jogo rodando" (processo do jogo sob o gamescope, uso da GPU etc.).
- Como detectar o cartão do R36S (rótulos `EASYROMS`/`BOOT`/`ROOTFS`, como na regra udev do guia).
- Visual da página (simples, legível no iPhone, tema escuro por ser usada na sala).

## Critérios de pronto

- Do iPhone, no Wi-Fi, a página abre pela tela de início, e "Reiniciar Sunshine" funciona com o modelo **desligado**.
- "O que está acontecendo?", com o Sunshine parado de propósito, diz que ele está parado e oferece o botão.
- Com um jogo aberto, o chat avisa antes de carregar o modelo. Depois de alguns minutos sem uso, a VRAM do modelo é liberada.
- "Organizar Downloads" com um arquivo de teste mostra o plano, só move depois de "Aprovar" e não toca em torrent ativo.
- Com o cartão do R36S no leitor, copia um arquivo de teste para o `EASYROMS`, e o `ROOTFS` continua sem montar.
- Um pedido fora da lista de ferramentas recebe "não sei fazer isso" em vez de uma resposta inventada.
- Capítulo novo no guia explicando a instalação e o uso.
