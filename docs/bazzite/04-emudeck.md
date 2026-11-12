# 04 · Emuladores (EmuDeck + ES-DE)

## Objetivo

Instalar os emuladores com configuração pronta e o ES-DE como frontend.

## Pré-requisitos

- Discos montados ([02](02-discos.md)).
- Fazer pelo **Modo Desktop**, na tela do próprio PC.

## Passos

1. **Instalar o EmuDeck.** O mais direto é `ujust get-emudeck` num terminal do PC. Pelo SSH ele falha, porque abre uma janela no fim. Alternativa: baixe o AppImage no GitHub oficial (EmuDeck/emudeck-electron), salve em `~/Applications` e dê permissão de execução.
2. **No assistente:** Custom Mode → dispositivo "Linux PC" → armazenamento Custom em `/var/mnt/roms`. Ele cria `Emulation/` com `roms`, `bios`, `saves` e `storage`. Se a janela não mostrar o `/var`, use Ctrl+L e digite o caminho.
3. **Frontend:** escolha ES-DE (o Steam ROM Manager continua disponível para favoritos). Na tela final, "Manual copy".
4. **Switch e PS3 no NVMe**, deixando links no lugar (com o EmuDeck fechado):

```bash
E=/var/mnt/roms/Emulation; N=/var/mnt/jogos/Emulation
mkdir -p $N/roms $N/storage
for p in roms/switch roms/ps3 storage/rpcs3 storage/ryujinx storage/eden; do
  [ -d "$E/$p" ] && [ ! -L "$E/$p" ] && mv "$E/$p" "$N/$p" && ln -s "$N/$p" "$E/$p"
done
```

5. **Switch:**
   - O "Ryujinx" do EmuDeck é o **Ryubing**, a continuação mantida.
   - **Eden** (opcional): o EmuDeck não baixa. Pegue o AppImage no site oficial (`stable.eden-emu.dev`, versão "amd64 PGO"), salve como `~/Applications/Eden.AppImage` e rode a configuração do EmuDeck:

```bash
source ~/.config/EmuDeck/backend/functions/all.sh; Eden_init
```

   - Keys: `bios/eden/keys` (Eden) e `~/.config/Ryujinx/system` (Ryujinx). O firmware se instala pelo menu de cada emulador.
   - **DLC não fica na pasta de ROMs:** instale pelo emulador (Eden: "Instalar arquivos na NAND").
   - Emulador padrão por sistema no ES-DE: Menu → Outras configurações → Emuladores alternativos.
6. **BIOS e firmware** em `Emulation/bios`, e rode o verificador de BIOS do EmuDeck. PS1 e PS2: BIOS. PS3: firmware oficial da Sony.

## Verificação

- ES-DE abre e lista os sistemas com jogos.
- Um jogo de teste (homebrew de GB/NES) abre e fecha pelo controle.

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| `ujust get-emudeck` falha pelo SSH | Precisa de janela gráfica | Rode na tela do PC, ou use o AppImage |
| Assistente do EmuDeck reaparece ao abrir | Não investigado | Use o ES-DE e o SRM direto |
| BotW "sem música" | O jogo é assim por design | Não é bug |
| Eden não aparece | O EmuDeck não baixa o Eden | Instalação manual + `Eden_init` |

**Switch 2 (Lichii):** experimental. Baixe **só** da página de releases do GitHub oficial (`zortos293/Lichii`). Sites com nomes parecidos (lichii.org e afins) não são do projeto, e há relato de malware.
