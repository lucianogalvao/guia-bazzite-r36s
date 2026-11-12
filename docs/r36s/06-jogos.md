# 06 · Escolher e copiar jogos

## Objetivo

Levar para o cartão novo só os jogos que você joga, com os saves, e reaproveitar a mesma seleção no EmuDeck do PC.

## Pré-requisitos

- Backup do cartão de fábrica ([02](02-backup.md)).
- Primeiro boot feito ([05](05-gravacao.md)).

## Passos

### Inventário e curadoria

1. Monte a EASYROMS do backup só para leitura e gere o inventário:

```bash
L=$(sudo losetup -r -P -f --show r36s-fabrica.img); sudo mount -o ro ${L}p3 /mnt/roms-fabrica
python3 ferramentas/curadoria/inventario.py /mnt/roms-fabrica > inv.json
python3 ferramentas/curadoria/agrupar.py inv.json roms.json
```

2. O `agrupar.py`:
   - Tira o lixo típico desses cartões: vídeos `.mp4`, configs do MAME (`.nv`, `.hi`), cache do PPSSPP, `.old`.
   - Junta as pastas duplicadas ("GB official game ROM complete works", "Featured Games", "top100") e as versões do mesmo jogo.
   - Marca protótipos, betas e hacks.
   - Sugere uma versão por jogo: PT-BR → USA → World → Europa → Japão, sem protótipos, e sempre a que tem save.
3. Escolha por **sistema** (manter ou cortar) e depois por **jogo**. Use o `roms.json` como quiser: numa planilha ou numa página simples.

No nosso caso: de ~21 mil arquivos em 27 sistemas sobraram **77 jogos (0,74 GB)**.

### Cópia para o cartão

4. Copie **só para a EASYROMS**, na pasta de cada sistema, com o `.srm` **ao lado** do jogo. No dArkOSRE, os saves ficam junto das ROMs.
5. Os 5 cartuchos de exemplo do PICO-8 podem sair. **Mantenha** os `Scan_for_new_games.*`, `tools/`, `themes/`, `bgmusic/` e `launchimages/`, que fazem parte do sistema.
6. Desmonte e tire o cartão:

```bash
sync; umount /run/media/$USER/EASYROMS /run/media/$USER/BOOT
```

### A mesma seleção no PC (EmuDeck)

7. ROMs em `Emulation/roms/<sistema>`. `.srm` em `Emulation/saves/retroarch/saves` (pasta única, mesmo nome da ROM). Veja [bazzite/05](../bazzite/05-biblioteca-srm.md).

## Verificação

- O R36S liga no menu com os sistemas novos. Se faltar algum, use Start → Atualizar lista de jogos.
- Um jogo com save (`.srm`) continua de onde parou.

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| Jogos de GB dentro da pasta do GBA | Cartão de fábrica bagunçado | Ignore as duplicatas |
| Arcade com nomes tipo `sf2.zip` | Nomes curtos do MAME | Procure no MAME para saber o jogo |
| Save state não carrega no PC | `.state` depende da versão do núcleo | Use o save do jogo (`.srm`) |
