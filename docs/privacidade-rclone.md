# Política de privacidade: rclone-bazzite

Última atualização: 12/11/2026

O **rclone-bazzite** é um cliente OAuth de **uso pessoal**, criado só para o dono deste repositório fazer o backup automático dos saves de emuladores do próprio PC para o próprio Google Drive. O processo está descrito em [docs/bazzite/11-backup-saves.md](bazzite/11-backup-saves.md). O app não é oferecido ao público.

## Quais dados o app acessa

- Pede só o escopo **`drive.file`**. Com ele, o app enxerga e altera **somente os arquivos e as pastas que ele mesmo criou** no Google Drive (a pasta `Bazzite-Saves`). Ele não tem acesso ao resto do Drive.
- Não pede acesso a e-mail, contatos, agenda, perfil ou qualquer outro dado da conta Google.

## Como os dados são usados

- Os arquivos enviados são saves de jogos do próprio usuário. Eles servem apenas como cópia de segurança.
- O token de acesso fica guardado só no computador do usuário, no arquivo de configuração do rclone (`~/.config/rclone/rclone.conf`, com permissão 600).

## Compartilhamento

- Nenhum dado é vendido, compartilhado ou enviado a terceiros.
- Não há servidor intermediário: o rclone fala direto com a API do Google Drive.

## Como revogar

Para tirar o acesso a qualquer momento, acesse [myaccount.google.com/permissions](https://myaccount.google.com/permissions) e remova o app **rclone-bazzite**. Os arquivos que já estão no Drive continuam lá até o usuário apagá-los.

## Contato

Abra uma issue neste repositório.
