# 06 · Extras: Battle.net e torrent

## Objetivo

Rodar o Battle.net (Diablo etc.) e baixar arquivos direto no HD, sem lotar o SSD do sistema.

## Pré-requisitos

- NVMe montado em `/var/mnt/jogos` e HD em `/var/mnt/roms`.

## Passos

### Battle.net pelo Lutris

1. Instale o Lutris e dê acesso ao NVMe:

```bash
sudo flatpak install flathub net.lutris.Lutris
flatpak override --user --filesystem=/var/mnt/jogos net.lutris.Lutris
```

2. No Lutris: "+" → procurar instaladores no site → "Battle.net — Standard".
3. **Leve o "C:" do Battle.net para o NVMe**, com o Battle.net e o Lutris fechados:

```bash
mkdir -p /var/mnt/jogos/Lutris
mv ~/Games/battlenet /var/mnt/jogos/Lutris/battlenet && ln -s /var/mnt/jogos/Lutris/battlenet ~/Games/battlenet
```

4. No Lutris, clique com o botão direito no Battle.net → "Criar atalho na Steam". Para abrir um jogo direto (ex.: Diablo IV), duplique a entrada e use os argumentos `--exec="launch Fen"`.
5. Para jogos da Epic ou da GOG: Heroic Launcher.

### qBittorrent

```bash
sudo flatpak install flathub org.qbittorrent.qBittorrent
flatpak override --user --filesystem=/var/mnt/roms org.qbittorrent.qBittorrent
```

Em Opções → Downloads, use `/var/mnt/roms/Downloads`, com uma subpasta para incompletos.

**Arquivos baixados:** confira o conteúdo antes de usar (`7z l`), descarte `.exe`, `.html` e afins, e valide ROMs contra o Redump ([05](05-biblioteca-srm.md)).

## Verificação

- `du -sh ~/Games` fica pequeno, porque os jogos estão no NVMe.
- O atalho do Battle.net abre pelo Game Mode.

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| Lutris não enxerga o NVMe | Rode o `flatpak override` acima |
| SSD do sistema enchendo | Confira se `~/Games/battlenet` é um link |
