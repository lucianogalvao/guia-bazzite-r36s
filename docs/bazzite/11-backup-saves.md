# 11 · Backup dos saves no Google Drive

## Objetivo

Copiar os saves de todos os emuladores para o Google Drive a cada 30 minutos, com histórico de versões, sem depender de ninguém lembrar.

## Pré-requisitos

- EmuDeck instalado ([04](04-emudeck.md)). Ele junta os saves em `Emulation/saves/<emulador>`, com links para a pasta real de cada um (os do Eden ficam na NAND, no NVMe).
- Uma conta Google.
- SSH configurado ([03](03-rede-wol.md)), se for fazer de outro computador.

## Passos

1. **Instale o rclone** pelo Homebrew do Bazzite (fica fora do sistema imutável):

```bash
brew install rclone
```

2. **Autorize o Google Drive.** O login é pelo navegador. Pelo SSH, abra um túnel e faça o login no navegador do outro computador:

```bash
# no outro computador
ssh -L 53682:127.0.0.1:53682 usuario@IP-DO-PC
# já dentro do PC: escopo drive.file (o rclone só enxerga o que ele mesmo criar)
rclone authorize drive "$(printf '{"scope":"drive.file"}' | base64 | tr -d '=' | tr '+/' '-_')" --auth-no-open-browser
```

   Abra o link `http://127.0.0.1:53682/auth?...` no navegador, autorize, e crie o remote com o token que aparecer (só o valor do campo `token` do bloco impresso):

```bash
rclone config create gdrive drive scope=drive.file token='<token>'
chmod 600 ~/.config/rclone/rclone.conf
```

3. **Instale o script e o timer** ([scripts/bazzite/backup-saves](../../scripts/bazzite/backup-saves), [config/bazzite/backup-saves.service](../../config/bazzite/backup-saves.service), [config/bazzite/backup-saves.timer](../../config/bazzite/backup-saves.timer)):

```bash
install -m 755 scripts/bazzite/backup-saves ~/.local/bin/
mkdir -p ~/.config/systemd/user
cp config/bazzite/backup-saves.{service,timer} ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now backup-saves.timer
loginctl enable-linger "$USER"     # roda mesmo sem sessão aberta (no Game Mode, por exemplo)
```

## Como fica no Drive

| Pasta | Conteúdo |
|---|---|
| `Bazzite-Saves/atual/` | Estado mais recente, separado por emulador |
| `Bazzite-Saves/historico/<data-hora>/` | Versão anterior de cada arquivo que mudou ou foi apagado |

O histórico guarda 90 dias (`RETENCAO` no script). É **só ida**: nada volta do Drive para o PC.

**Para restaurar:** baixe o arquivo do Drive (de `atual` ou de uma data em `historico`) e copie para a mesma pasta em `Emulation/saves/<emulador>/`, com o emulador fechado.

## Verificação

```bash
systemctl --user list-timers backup-saves.timer      # próxima execução
journalctl --user -u backup-saves.service -n 20      # último backup
rclone size gdrive:Bazzite-Saves/atual
```

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| Aviso "shared Google Drive client_id ... being retired" | O client_id compartilhado do rclone vai ser desativado pelo Google | Crie um client_id próprio (rclone.org/drive/#making-your-own-client-id) e refaça o passo 2 com `client_id=` e `client_secret=` |
| "directory not found" na primeira execução | Ainda não existia o histórico | Corrigido no script: a limpeza só roda se a pasta existir |
| Backup cancelado: "Disco não montado" | HD ou NVMe não montou | Proposital: sem o disco, o `sync` apagaria os saves do Drive. Veja [02](02-discos.md) |
| Save state não funciona em outro aparelho | Save state depende do núcleo e da versão | Normal. Os saves do jogo (`.srm`, NAND) funcionam |
