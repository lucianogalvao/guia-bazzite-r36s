# 02 · Backup do cartão de fábrica

## Objetivo

Guardar uma cópia exata do cartão original antes de qualquer mudança.

## Pré-requisitos

- Leitor USB de microSD.
- Espaço livre igual ao tamanho do cartão (o nosso: ~52 GB).
- Regra do [01](01-antes-de-tudo.md) instalada. O cartão de fábrica usa ext4 e não sofre do problema do btrfs, mas é bom hábito.

## Passos

1. Identifique o cartão e **desmonte** todas as partições. O sistema monta sozinho ao inserir:

```bash
lsblk -o NAME,SIZE,TRAN,RM,MODEL,FSTYPE,LABEL,MOUNTPOINTS
for p in /dev/sdX1 /dev/sdX2 /dev/sdX3; do udisksctl unmount -b $p; done
```

2. Rode o `dd` **como serviço do systemd**. Com `nohup`, a cópia morre junto com a sessão SSH:

```bash
sudo systemd-run --unit=r36s-backup --collect sh -c \
  "dd if=/dev/sdX of=/caminho/backup/r36s-fabrica.img bs=1M conv=noerror,sync status=progress > /caminho/backup/dd.log 2>&1"
```

3. Acompanhe:

```bash
systemctl is-active r36s-backup; tr '\r' '\n' < /caminho/backup/dd.log | tail -1
```

4. Guarde o `.dtb` e o `boot.ini` da partição BOOT de fábrica. Eles servem para descobrir a variante ([04](04-variante.md)).

## Verificação

- O tamanho do `.img` é igual ao de `blockdev --getsize64 /dev/sdX`, e o log mostra `N+0 registos` (sem `+1`).
- As partições dentro da imagem passam numa checagem só de leitura:

```bash
L=$(sudo losetup -r -P -f --show r36s-fabrica.img)
sudo fsck.vfat -n ${L}p1; sudo e2fsck -fn ${L}p2; sudo ntfsfix -n ${L}p3
sudo losetup -d $L
```

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| `I/O error ... Incompatible medium installed` ao inserir | Leitura momentânea do leitor | Teste o setor de novo com `dd skip=N count=64`. Se ler, siga |
| ~10 MB/s | Leitor USB 2.0 ou cartão de fábrica lento | Normal: ~1h30 para 52 GB |
| Cópia parou em segundos | `dd` morreu com a sessão SSH | Use `systemd-run` |

O cartão de fábrica tinha BOOT (vfat 112 MB), root (ext4 6,5 GB) e EASYROMS (**NTFS** 42 GB, 100% cheio), com restos de ferramentas de Windows na raiz (`EUMONBMP.SYS`, `{GUID}.CBM`), inofensivos.
