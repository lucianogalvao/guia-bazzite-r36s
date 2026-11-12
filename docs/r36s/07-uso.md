# 07 · Uso no dia a dia

## Objetivo

Atalhos do RetroArch no dArkOSRE.

## Atalhos

Tirados do `retroarch.cfg` do dArkOSRE 03082026, com o mapa do controle "GO-Super Gamepad" (variante Y3506). **São diferentes do ArkOS antigo**, em que era Select + R1/L1.

| Atalho (segure o Select) | Ação |
|---|---|
| **Select + B** | Salvar state |
| **Select + A** | Carregar state |
| **Select + X** / **Select + Y** | Próximo slot / slot anterior |
| **Select + Start** | Sair do jogo |
| **Select + →** | Acelerar (fast forward) |
| **Select + ←** | Voltar no tempo (rewind) |
| **Select + FN** ou **L1 + R1 + Start + Select** | Menu do RetroArch |

O Nintendo DS roda pelo DraStic, que tem menu próprio.

## Como conferir na sua imagem (sem root e sem montar)

Extraia a partição `ROOTFS` da imagem e leia os arquivos com `btrfs restore`:

```bash
dd if=dArkOSRE_R36_trixie_03082026.img of=rootfs.img bs=512 skip=237568 count=15360000
btrfs restore --path-regex '^/(|home(|/ark(|/\.config(|/retroarch(|/retroarch\.cfg)))))$' rootfs.img saida/
grep -E '^input_(enable_hotkey|save_state|load_state|exit_emulator|menu_toggle)_btn' saida/home/ark/.config/retroarch/retroarch.cfg
```

Os números dos botões estão em `home/ark/.config/retroarch/autoconfig/udev/GO-Super Gamepad.cfg`. O nome do controle está no `.dtb` (`joypad-name`).

## Verificação

- Select + B mostra "Estado salvo" na tela.

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| Tela preta ao sair do jogo, com a música tocando | Toque curto no botão de ligar para suspender e outro para acordar ([08](08-problemas.md)) |
