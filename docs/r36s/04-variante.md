# 04 · Descobrir a variante sem abrir o aparelho

## Objetivo

Escolher a configuração de tela e placa (`.dtb`) certa entre as ~30 do dArkOSRE, sem desmontar o R36S.

## Pré-requisitos

- O `.dtb` da partição BOOT de fábrica. O `boot.ini` diz qual é usado (o nosso: `rk3326-r35s-linux.dtb`).
- `dtc` (`brew install dtc`) e a imagem do dArkOSRE.

## Passos

1. Monte a partição BOOT da imagem do dArkOSRE só para leitura e liste as variantes em `dtb/{r36s,clone,soysauce}/`:

```bash
sudo mount -o ro,loop,offset=$((32768*512)) dArkOSRE_R36_trixie_03082026.img /mnt/darkos
find /mnt/darkos/dtb -name rk3326-r36s-linux.dtb
```

2. Rode o [`scripts/r36s/comparar-dtb.sh`](../../scripts/r36s/comparar-dtb.sh). Ele compara o bloco do painel (`panel@0`) e o arquivo inteiro com cada candidata e ordena da mais parecida para a menos:

```bash
scripts/r36s/comparar-dtb.sh rk3326-r35s-linux.dtb /mnt/darkos/dtb
```

3. Leia o resultado:
   - A **família** aparece logo. No nosso caso, a soysauce ficou com 30 a 52 linhas de diferença, contra mais de 760 nas outras.
   - Entre as finalistas, priorize a **temporização da tela** (`hback-porch`, `hfront-porch`, `vback-porch`, `vfront-porch`, `hsync-len`, `vsync-len`). Com a temporização errada, a tela fica preta ou deslocada. Botões e tabela da bateria são ajustes menores.
   - A `panel-init-sequence` de fábrica pode ser mínima (só "acordar e ligar") e não serve para desempatar.

| Candidata | Temporização da tela | Botões | Bateria |
|---|---|---|---|
| `soysauce/Y3506_V05_20251215 2551` | ✅ igual à de fábrica | 2 trocados | diferente |
| `soysauce/Y3506_V05_20251215 2601` | ❌ diferente | ✅ iguais | ✅ igual |

A **2551** foi a certa: tela, botões e som funcionaram.

## Verificação

- O primeiro boot mostra o logo e chega ao menu ([05](05-gravacao.md)).
- O log `darkosre_device.log` da partição BOOT mostra `Hardware string: '<variante>'` e a família certa.

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| Tela preta no **primeiro** boot | Variante errada: troque os `.dtb` da raiz do BOOT pela próxima candidata. Não é preciso regravar |
| Tela preta depois de já ter funcionado | Não é a variante. Veja [01](01-antes-de-tudo.md) |

Abrir o aparelho também resolve: o código da placa fica impresso perto da bateria ou do conector da tela (ex.: `R36S-V12 2023-08-18`, `G80CA-MB V1.2`, `Y3506_V05`).
