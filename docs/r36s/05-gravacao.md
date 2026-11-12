# 05 · Gravar o dArkOSRE e primeiro boot

## Objetivo

Gravar a imagem num cartão novo, instalar a variante e completar o primeiro boot.

## Pré-requisitos

- Regra do [01](01-antes-de-tudo.md) instalada.
- Cartão novo de marca (64 GB+), testado contra falsificação ([08](08-problemas.md)).
- Imagem conferida ([03](03-download.md)) e variante escolhida ([04](04-variante.md)).
- **Não use o balenaEtcher**: o guia oficial pede para evitar.

## Passos

1. Rode o [`scripts/r36s/regravar-cartao.sh`](../../scripts/r36s/regravar-cartao.sh). Num cartão novo, informe o `DEV` (confira com `lsblk`). Num cartão que já tem dArkOSRE, ele acha sozinho pelo rótulo `ROOTFS`:

```bash
sudo DEV=/dev/sdX \
     IMG=/caminho/dArkOSRE_R36_trixie_03082026.img \
     SHA=a4858eee2f1eced10d3ce90c911d89450eea700f \
     DTB="dtb/soysauce/Y3506_V05_20251215 2551" \
     bash scripts/r36s/regravar-cartao.sh
```

   O script:
   - Instala a regra do [01](01-antes-de-tudo.md).
   - Acha o cartão pelo rótulo `ROOTFS` e **aborta** se o disco não for USB removível com menos de 70 GB.
   - Desmonta, grava com `dd` (~5 min a ~30 MB/s) e confere o SHA1 relendo o cartão.
   - Na partição BOOT: apaga os `.dtb` da raiz e copia os da variante. É o mesmo que o "SELECT MODEL.bat" faz no Windows.
   - Ejeta o cartão.

2. **Primeiro boot no R36S:**
   - Cartão no slot **TF1** e o segundo slot vazio.
   - **Sem carregador.**
   - Espere chegar no **menu com música**. Ele expande o `ROOTFS`, converte a EASYROMS para exFAT com o espaço restante e reinicia sozinho.
3. Desligue pelo menu (Start → Desligar) antes de tirar o cartão.

## Verificação

- Menu do EmulationStation com música, botões e som funcionando.
- No PC, ao reinserir o cartão, só `BOOT` e `EASYROMS` montam:

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS /dev/sdX
# sdX1 100M vfat BOOT, sdX2 ~10G btrfs ROOTFS (SEM montagem), sdX3 exfat EASYROMS
```

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| Logo e tela preta no primeiro boot | Variante errada ([04](04-variante.md)) |
| Logo e tela preta depois de ter funcionado | O PC montou o `ROOTFS` ([01](01-antes-de-tudo.md)) |
| `udisksctl mount` falha pelo SSH ("Not authorized") | Use `sudo mount` |
