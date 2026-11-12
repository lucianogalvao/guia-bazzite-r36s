# 05 · Biblioteca e Steam ROM Manager

## Objetivo

Organizar as ROMs, trazer saves de outros aparelhos e pôr os favoritos direto na Steam.

## Pré-requisitos

- EmuDeck instalado ([04](04-emudeck.md)).
- ROMs e BIOS obtidas por conta própria.
- **A Steam fechada** sempre que o SRM for gravar atalhos.

## Passos

### ROMs

1. Copie para `Emulation/roms/<sistema>`. O ES-DE encontra os jogos novos ao abrir.
2. Use formatos compactos: **CHD** para PS1/PS2/Dreamcast e **RVZ** para GameCube/Wii. O `chdman` vem com o EmuDeck:

```bash
C=/var/mnt/roms/Emulation/tools/chdconv/chdman5
$C createcd -i "Jogo (USA).cue" -o "Jogo (USA).chd" && $C verify -i "Jogo (USA).chd"
```

3. **Confira dumps baixados** contra o Redump. O libretro mantém uma cópia do banco no GitHub (`libretro/libretro-database`, `metadat/redump/`). Compare o tamanho e o CRC do `.bin`:

```bash
7z l -slt "Jogo (USA).7z" | grep -E "^(Path|Size|CRC) ="
grep -A4 'Jogo (USA)' "Sony - PlayStation.dat"
```

### Saves vindos de outro aparelho

4. Saves do jogo do RetroArch (`.srm`) vão todos juntos em `Emulation/saves/retroarch/saves`, **com o mesmo nome da ROM**. Funcionam entre aparelhos.
5. Save states (`.state`) só funcionam no mesmo núcleo e na mesma versão. Não vale a pena copiar.

### Steam ROM Manager (SRM)

6. Se o EmuDeck não instalou o SRM, baixe o AppImage do GitHub oficial (SteamGridDB/steam-rom-manager) e salve em `Emulation/tools/Steam-ROM-Manager.AppImage`.
7. Settings → Theme: **Classic**. O tema do EmuDeck esconde a edição dos parsers e os erros.
8. Corrija os modelos do EmuDeck, que vêm com caminhos do Steam Deck:

```bash
sed -i "s#/home/deck/#$HOME/#g" ~/.config/steam-rom-manager/userData/userConfigurations.json
```

   Se a pasta do sistema for um link (Switch/PS3 no NVMe), use o caminho real em "ROMs directory".
9. Test parser → Add Games → Parse → Save to Steam.

### SRM pelo terminal (útil via SSH)

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u) WAYLAND_DISPLAY=wayland-1 DISPLAY=:0
export XAUTHORITY=$(ls /run/user/$(id -u)/xauth_* | head -1)
A=/var/mnt/roms/Emulation/tools/Steam-ROM-Manager.AppImage
$A list
```

Exemplo: atalho só para a série Mario Party (N64 pelo RetroArch). Valores que começam com `-` vão com `=`:

```bash
CORE=$HOME/.var/app/org.libretro.RetroArch/config/retroarch/cores/mupen64plus_next_libretro.so
$A create --ptype Glob-regex --name "Nintendo 64 - Mario Party (RetroArch)" \
  --rom-directory /var/mnt/roms/Emulation/roms/n64/ \
  --glob-regex '${/(Mario Party.*)\.n64/}' \
  --executable /var/mnt/roms/Emulation/tools/launchers/retroarch.sh \
  "--executable-args=-L \"$CORE\" \"\${filePath}\"" \
  --steam-categories "Nintendo 64" --image-providers sgdb steamCDN
$A add --only <id-do-parser>
```

## Verificação

- No Game Mode, os jogos aparecem em "Não-Steam" e numa coleção, com capa, e abrem direto no emulador.
- O save do jogo carrega de onde parou.

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| "config ignorada" / "invalid configuration" | Caminhos `/home/deck` | Use o `sed` acima e corrija os campos em vermelho |
| Mudanças no parser somem | O SRM aberto sobrescreve o arquivo | Edite com o SRM fechado |
| CLI do SRM: "Missing X server" | Falta o `XAUTHORITY` | Exporte as variáveis acima |
| CLI do SRM: "Unknown option --L" | Valor começando com `-` | Use `--executable-args=...` |
