# 08 · Problemas e soluções (R36S)

## Formato

Cada problema tem: **sintoma** → **diagnóstico** → **causa** → **solução**.

---

## Logo do dArkOSRE e depois tela preta, sem música (boot)

- **Diagnóstico:** no PC, o `darkosre_device.log` da partição BOOT não ganha linhas novas, ou o `ROOTFS` não tem arquivos alterados depois do último boot bom. O relógio do R36S é falso (sem RTC), então compare a ordem dos arquivos, não a data.
- **Causa:** o PC montou o `ROOTFS` (btrfs) do cartão.
- **Solução:** [01 · Antes de tudo](01-antes-de-tudo.md).

## Tela preta ao sair de um jogo, com a música tocando

- **Causa:** a tela não reinicializa quando o emulador fecha nessa variante (Y3506_V05 2551). O EmulationStation continua rodando.
- **Contorno:** um toque curto no botão de ligar (suspende) e outro (acorda). A imagem volta.
- **Correção definitiva:** não encontrada. Exigiria mexer no `ROOTFS`, e o R36S não tem Wi-Fi.

## Cartão "SanDisk 64 GB" com ~50 GB

- **Diagnóstico:** `sudo blockdev --getsize64 /dev/sdX` mostrou 53.739.520.000 bytes, e o próprio R36S também criou as partições contando ~50 GB. Um SanDisk 64 GB original tem uns 59,5 GB.
- **Causa:** cartão quase certamente falsificado (comum em marketplace). O cartão que vem com o R36S também costuma ser.
- **O tipo perigoso** é o que anuncia mais do que tem: os dados somem sem aviso. Para testar, rode [`scripts/r36s/teste-cartao-falso.py`](../../scripts/r36s/teste-cartao-falso.py). Ele **apaga o cartão**: grava 512 blocos marcados espalhados pelo espaço anunciado e relê sem cache. Um cartão que "dá a volta" no espaço real corrompe os blocos.

```bash
sudo python3 scripts/r36s/teste-cartao-falso.py /dev/sdX
# tamanho=53.74 GB blocos=512 ruins=0  → o espaço anunciado é real
```

- O pacote `f3` do Homebrew para Linux vem sem o `f3probe`, só com `f3write`/`f3read`, que levam horas.

## Erros "Incompatible medium installed" no leitor USB

- **Causa:** leitor genérico (Genesys `05e3:0747`), em especial perto do fim do cartão.
- **Solução:** releia o setor. Se ler, siga. Confira toda gravação pelo SHA1.

## Arquivo editado no `ROOTFS` pelo PC sumiu ou quebrou o boot

- **Causa:** gravado com zstd, que o kernel 4.4 não lê, e ainda liga o bit `0x10` na partição.
- **Solução:** regravar ([05](05-gravacao.md)). **Não edite o `ROOTFS` pelo PC.** Para ler, use `btrfs restore` sobre uma cópia ([07](07-uso.md)).

## O log do EmulationStation não existe

- `LogLevel` vem `disabled` em `~/.emulationstation/es_settings.cfg`. Mudar exige editar o `ROOTFS` (veja o item acima).
