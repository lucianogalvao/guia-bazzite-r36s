# 12 · Comandos do dia a dia

## Objetivo

Ter num lugar só os comandos para cuidar do PC console à mão: ver se está tudo de pé, destravar o streaming, organizar ROMs, fazer backup dos saves e abastecer o R36S. Servem tanto no terminal do PC quanto pelo SSH.

## Pré-requisitos

- SSH configurado ([03](03-rede-wol.md)). De outro computador: `ssh usuario@IP-DO-PC`.
- Discos em `/var/mnt/roms` (HD) e `/var/mnt/jogos` (NVMe) ([02](02-discos.md)).

## Status geral

```bash
findmnt /var/mnt/roms /var/mnt/jogos                             # os dois discos montados?
df -h /var/mnt/roms /var/mnt/jogos ~                              # espaço livre
systemctl --user is-active app-dev.lizardbyte.app.Sunshine        # Sunshine rodando? (active)
systemctl --user list-timers backup-saves.timer                   # próximo backup dos saves
nvidia-smi --query-gpu=memory.used,memory.total --format=csv      # memória de vídeo em uso
nvidia-smi | sed -n '/Processes/,$p'                              # o que está usando a GPU (jogo aberto?)
```

## Streaming (Sunshine)

O caso mais comum: o Moonlight dá erro na TV. Quase sempre o problema é o Sunshine, e reiniciar resolve.

```bash
systemctl --user restart app-dev.lizardbyte.app.Sunshine         # reiniciar
systemctl --user status app-dev.lizardbyte.app.Sunshine --no-pager
journalctl --user -u app-dev.lizardbyte.app.Sunshine --since -10min -o cat | tail -40   # últimos logs
```

Para ler o log, procure por estas mensagens (as soluções estão em [10](10-problemas.md)):

| No log | Significa |
|---|---|
| `Couldn't find monitor` / `Fatal` | Perdeu a tela (erro 503). Reinicie |
| `Couldn't connect to Wayland display` | Sunshine iniciado no modo errado (Desktop × Game Mode). Reinicie no modo certo |
| `libx264 [software]` | Caiu para o encoder por CPU: stream pesado. Veja [07](07-sunshine.md), passo 4 |

Fechar um jogo ou emulador travado (o que não foi salvo se perde):

```bash
nvidia-smi | sed -n '/Processes/,$p'     # ache o PID do jogo
kill -TERM <PID>                         # pede para fechar; se não fechar em ~10 s: kill -KILL <PID>
```

Trocar de modo sem mouse:

```bash
steamos-session-select gamescope   # Game Mode
steamos-session-select plasma      # Modo Desktop
```

## Backup dos saves

Detalhes em [11](11-backup-saves.md).

```bash
systemctl --user start backup-saves.service                       # backup agora
journalctl --user -u backup-saves.service -n 20 -o cat            # como foi o último
rclone lsd gdrive:Bazzite-Saves/historico                         # versões guardadas
```

Para restaurar, baixe o arquivo do Drive e copie para `Emulation/saves/<emulador>/`, com o emulador fechado.

## ROMs

Os downloads do qBittorrent caem em `/var/mnt/roms/Downloads`. As regras completas estão em [05](05-biblioteca-srm.md).

1. **Ver o que chegou e o que tem dentro dos compactados:**

```bash
cd /var/mnt/roms/Downloads
find . -type f -size +5M -printf "%10s  %p\n" | sort -k2
7z l -ba "Pasta/Jogo.7z"
```

2. **Antes de apagar ou mover algo, confira se o torrent ainda está semeando.** No qBittorrent, o status aparece na lista. Apagar o arquivo de um torrent ativo deixa o torrent com erro. Se quiser continuar semeando, **extraia ou copie** e deixe o original no lugar.

3. **Extrair para a pasta do sistema.** O `7z x` confere o CRC ao extrair:

```bash
R=/var/mnt/roms/Emulation/roms
7z x -aos -o"$R/snes" "Jogo (USA).7z"                  # -aos: não sobrescreve o que já existe
```

4. **CD de PS1/PS2/Dreamcast/Saturn em CHD** (economiza espaço, um arquivo só):

```bash
C=/var/mnt/roms/Emulation/tools/chdconv/chdman5
$C createcd -i "Jogo (USA).cue" -o "$R/psx/Jogo (USA).chd" && $C verify -i "$R/psx/Jogo (USA).chd"
```

5. **Switch:** o jogo (`.xci`/`.nsp`) vai para `/var/mnt/jogos/Emulation/roms/switch/`. **Updates e DLCs não vão na pasta de ROMs**, senão o ES-DE os lista como jogos. Deixe-os em `/var/mnt/jogos/Emulation/switch-extras/<Jogo>/` e instale no Eden: Arquivo → "Instalar arquivos na NAND...", selecionando todos os `.nsp` da pasta. Depois de instalados, os `.nsp` de `switch-extras` podem ser apagados.

6. **Tarefas demoradas sem ficar preso ao SSH.** Rode em segundo plano, com log. A tarefa continua mesmo se a conexão cair:

```bash
nohup setsid meu-script.sh > ~/meu-script.log 2>&1 < /dev/null &
tail -f ~/meu-script.log          # acompanhar (Ctrl+C só para de acompanhar)
```

## R36S (cartão no leitor do PC)

**Regra de ouro:** só se mexe na partição `EASYROMS`. A partição `ROOTFS` (sistema, btrfs) **nunca** pode ser montada pelo PC. Ver [r36s/01](../r36s/01-antes-de-tudo.md).

1. **Conferir o cartão:**

```bash
lsblk -o NAME,SIZE,LABEL,FSTYPE,MOUNTPOINT
```

   O esperado: `EASYROMS` e `BOOT` montadas em `/run/media/$USER/`, e `ROOTFS` **sem** ponto de montagem. Se o `ROOTFS` aparecer montado, desmonte na hora (`umount`) e reveja a regra udev do [r36s/01](../r36s/01-antes-de-tudo.md).

2. **Copiar jogos, com o save ao lado da ROM:**

```bash
E=/run/media/$USER/EASYROMS
cp -n "Jogo (USA).gba" "Jogo (USA).srm" "$E/gba/"
```

3. **BIOS:** em `EASYROMS/bios/`. Copie só os arquivos que faltam (`cp -n`).

4. **Tirar o cartão com segurança:**

```bash
sync; umount /run/media/$USER/EASYROMS /run/media/$USER/BOOT
```

## Verificação

- `systemctl --user is-active app-dev.lizardbyte.app.Sunshine` responde `active` e o Moonlight conecta.
- O ES-DE mostra os jogos novos e o Eden mostra os updates na coluna "Add-ons".
- No R36S, Start → Atualizar lista de jogos mostra o que foi copiado.

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| `Permission denied` em `/var/mnt/...` | O dono do disco precisa ser o seu usuário: `sudo chown "$USER:" /var/mnt/roms /var/mnt/jogos` |
| `systemctl --user` reclama de bus pelo SSH | `export XDG_RUNTIME_DIR=/run/user/$(id -u)` |
| Jogo não aparece no ES-DE | Pasta errada do sistema: confira os nomes em `Emulation/roms/` |
| Torrent com "arquivos faltando" | O arquivo foi movido ou apagado. Devolva-o, ou remova o torrent no qBittorrent |
