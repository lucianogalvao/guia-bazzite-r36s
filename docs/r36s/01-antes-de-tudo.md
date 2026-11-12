# 01 · Antes de tudo: não deixe o PC montar o sistema do cartão

## Objetivo

Evitar o erro mais caro desta montagem: o portátil mostra o logo do dArkOSRE e depois fica com a tela preta, sem menu e sem música.

## O que acontece

| | R36S (dArkOSRE 03082026) | PC com Bazzite |
|---|---|---|
| Kernel | **4.4.189** (2016) | 7.x |
| Partição do sistema do cartão | `ROOTFS`, btrfs | monta sozinho ao inserir o cartão |

Ao montar o `ROOTFS` do cartão, o Bazzite usa `space_cache=v2,compress-force=zstd`. Duas consequências:

1. **Free space tree** (`compat_ro_flags 0x3`): criado só por montar em leitura e escrita. O kernel 4.4 não conhece esse recurso (veio no 4.5) e passa a montar o sistema **só para leitura**. O menu não abre.
2. **Bit do zstd** (`incompat_flags` com `0x10`): ligado só por montar com a opção de zstd, **mesmo sem gravar nada**. O kernel 4.4 não suporta zstd no btrfs (veio no 4.14) e **recusa montar**. O boot para logo depois do logo.

A imagem limpa do dArkOSRE tem `compat_ro_flags 0x0` e `incompat_flags 0x361`.

## Pré-requisitos

- Acesso de administrador no PC.

## Passos

O Bazzite tem **dois montadores automáticos**: o do KDE/udisks e o herdado do SteamOS (`/usr/lib/udev/rules.d/99-steamos-automount.rules`). Uma regra que só usa `UDISKS_IGNORE` não para o segundo. A regra precisa rodar **antes** dele (número 98) e mudar o `ID_FS_USAGE`:

```bash
sudo install -m644 config/r36s/98-r36s-no-automount.rules /etc/udev/rules.d/
sudo udevadm control --reload
```

A regra vale só para uma partição **btrfs** chamada **ROOTFS** num dispositivo **USB**. As partições `BOOT` (vfat) e `EASYROMS` (exFAT) continuam montando normalmente, e é por elas que se copia jogos e se troca a variante.

## Verificação

Insira o cartão e confira:

```bash
lsblk -o NAME,FSTYPE,LABEL,MOUNTPOINTS /dev/sdX
udevadm info -q property -n /dev/sdX2 | grep -E "ID_FS_USAGE|UDISKS_IGNORE"
```

`ROOTFS` precisa ficar **sem ponto de montagem**, com `ID_FS_USAGE=r36s-ignorar`.

## Se já aconteceu

Confira os bits (precisa de root):

```bash
sudo btrfs inspect-internal dump-super /dev/disk/by-label/ROOTFS | grep -E "^(compat_ro|incompat)_flags"
```

| Resultado | O que fazer |
|---|---|
| `compat_ro 0x3`, `incompat` **sem** `0x10` | Rode [`scripts/r36s/limpar-free-space-tree.sh`](../../scripts/r36s/limpar-free-space-tree.sh) |
| `incompat` **com** `0x10` | Regrave o cartão ([05](05-gravacao.md)). As ferramentas não desligam esse bit |

**Nunca edite arquivos do `ROOTFS` pelo PC.** Um arquivo gravado com zstd fica ilegível para o R36S.
