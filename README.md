# Guia: PC console com Bazzite + portátil R36S com dArkOSRE

Anotações práticas de duas montagens feitas em casa, com tudo o que deu certo, o que deu errado e como foi resolvido:

1. **Um PC parado vira console de sala.** Bazzite no Game Mode, Steam e emuladores (EmuDeck + ES-DE), transmitidos para a TV por Sunshine + Moonlight num Fire TV Stick.
2. **Um portátil R36S troca o sistema de fábrica pelo dArkOSRE**, com backup do cartão original, descoberta da variante sem abrir o aparelho e a mesma seleção de jogos do PC.

Nada aqui inclui ROMs, BIOS, chaves ou firmware. Use só o que você tem direito de usar.

## Hardware usado

| Peça | Modelo |
|---|---|
| CPU / RAM | Intel i5-10400F, 32 GB DDR4 (limitada a 2666 MHz na H510) |
| GPU | NVIDIA RTX 3060 Ti |
| Placa-mãe | ASUS PRIME H510M-A (rede Realtek gigabit, sem Wi-Fi/BT) |
| Discos | SSD SATA 240 GB (sistema), NVMe 1 TB (jogos), HD 1 TB (ROMs e backups) |
| Bluetooth | Dongle USB Realtek RTL8761B |
| Controles | 2x Xbox Series (modelo 1914) |
| Sala | Fire TV Stick 4K Max (2ª geração), TV Samsung AU7700 (2021, Tizen 6.0) |
| Portátil | R36S variante "Soy Sauce" (placa Y3506) |

## Como ler

Cada documento segue o mesmo formato: **Objetivo**, **Pré-requisitos**, **Passos**, **Verificação** e **Problemas conhecidos**. Os comandos usam marcadores que você troca pelos seus valores:

| Marcador | Significado |
|---|---|
| `IP-DO-PC` | IP fixo do PC na rede local |
| `IP-DA-TV` | IP da TV |
| `SAIDA-DE-VIDEO` | Saída do monitor no PC, ex.: `DP-3` (veja com `kscreen-doctor -o`) |
| `/dev/sdX` | Disco do cartão no leitor USB. Confira sempre com `lsblk` antes de gravar |

## Índice

### PC com Bazzite

| # | Documento | Assunto |
|---|---|---|
| 01 | [Instalação](docs/bazzite/01-instalacao.md) | BIOS, ISO, instalador, primeiro boot |
| 02 | [Discos](docs/bazzite/02-discos.md) | NVMe e HD em ext4, montagem, biblioteca Steam |
| 03 | [Rede e Wake-on-LAN](docs/bazzite/03-rede-wol.md) | IP fixo, WoL, SSH, Alexa |
| 04 | [Emuladores](docs/bazzite/04-emudeck.md) | EmuDeck, ES-DE, Switch, Switch e PS3 no NVMe |
| 05 | [Biblioteca e Steam ROM Manager](docs/bazzite/05-biblioteca-srm.md) | ROMs, CHD, saves, atalhos na Steam |
| 06 | [Extras](docs/bazzite/06-extras.md) | Battle.net (Lutris), qBittorrent |
| 07 | [Sunshine](docs/bazzite/07-sunshine.md) | Servidor de streaming no Game Mode |
| 08 | [Moonlight no Fire TV Stick](docs/bazzite/08-fire-tv.md) | Cliente principal na sala |
| 09 | [Moonlight direto na TV Samsung](docs/bazzite/09-tv-samsung.md) | Plano B sem Fire Stick |
| 10 | [Problemas e soluções](docs/bazzite/10-problemas.md) | Tela escura, erro 503, tela preta, suspensão |

### Portátil R36S com dArkOSRE

| # | Documento | Assunto |
|---|---|---|
| 01 | [Antes de tudo](docs/r36s/01-antes-de-tudo.md) | **Leia primeiro:** o PC Linux pode estragar o sistema do cartão |
| 02 | [Backup do cartão de fábrica](docs/r36s/02-backup.md) | Imagem completa com `dd` |
| 03 | [Baixar o dArkOSRE](docs/r36s/03-download.md) | Fontes oficiais e SHA1 |
| 04 | [Descobrir a variante](docs/r36s/04-variante.md) | Comparar o `.dtb` sem abrir o aparelho |
| 05 | [Gravar e primeiro boot](docs/r36s/05-gravacao.md) | `dd`, conferência, variante, primeiro boot |
| 06 | [Escolher e copiar jogos](docs/r36s/06-jogos.md) | Curadoria, ROMs, saves |
| 07 | [Uso no dia a dia](docs/r36s/07-uso.md) | Atalhos de save state, sair do jogo |
| 08 | [Problemas e soluções](docs/r36s/08-problemas.md) | Tela preta, cartão falso, leitor USB |

## Scripts e configurações

| Caminho | O que é |
|---|---|
| [`scripts/bazzite/sunshine-start`](scripts/bazzite/sunshine-start) | Inicia o Sunshine com o display certo no Game Mode |
| [`scripts/bazzite/sunshine-res`](scripts/bazzite/sunshine-res) | Troca a resolução para 1080p durante o streaming |
| [`config/bazzite/`](config/bazzite/) | Drop-ins do serviço, retomada após suspensão, regra de sudo para a Alexa |
| [`scripts/r36s/regravar-cartao.sh`](scripts/r36s/regravar-cartao.sh) | Grava o dArkOSRE, confere e instala a variante |
| [`scripts/r36s/limpar-free-space-tree.sh`](scripts/r36s/limpar-free-space-tree.sh) | Desfaz o free space tree criado pelo PC |
| [`scripts/r36s/teste-cartao-falso.py`](scripts/r36s/teste-cartao-falso.py) | Teste rápido de cartão falsificado |
| [`scripts/r36s/comparar-dtb.sh`](scripts/r36s/comparar-dtb.sh) | Acha a variante mais parecida com o `.dtb` de fábrica |
| [`config/r36s/98-r36s-no-automount.rules`](config/r36s/98-r36s-no-automount.rules) | Impede o PC de montar o sistema do cartão |
| [`ferramentas/curadoria/`](ferramentas/curadoria/) | Inventário das ROMs agrupado por jogo e versão |

## Pendências conhecidas

- O Sunshine nem sempre acompanha a troca entre Game Mode e Modo Desktop. O contorno é reiniciar o serviço. Veja [Problemas](docs/bazzite/10-problemas.md).
- Desligar o HDR do Game Mode deixa o stream preto no Sunshine 2026.914 (issue upstream LizardByte/Sunshine#5839).
- No R36S Y3506, sair de um jogo pode deixar a tela preta. O contorno é suspender e acordar.
