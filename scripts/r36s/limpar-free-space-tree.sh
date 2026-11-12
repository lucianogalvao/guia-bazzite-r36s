#!/usr/bin/bash
# limpar-free-space-tree.sh — desfaz o free space tree que um kernel novo cria ao montar o
# ROOTFS (btrfs) do R36S, e diz se o bit do zstd também foi ligado (aí só regravando).
#
# Uso: sudo bash limpar-free-space-tree.sh
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Rode com sudo"; exit 1; }

P=/dev/disk/by-label/ROOTFS
[ "$(lsblk -no FSTYPE $P)" = btrfs ] && [ "$(lsblk -dno TRAN "/dev/$(lsblk -no PKNAME $P)")" = usb ] \
  || { echo "ABORTADO: ROOTFS não é o btrfs de um cartão USB"; exit 1; }

umount $P 2>/dev/null || true
findmnt -rn -S $P >/dev/null && { echo "ABORTADO: ROOTFS ainda montado"; exit 1; }

echo "== antes"
btrfs inspect-internal dump-super $P | grep -E "^(compat_ro_flags|incompat_flags)"

btrfs rescue clear-space-cache v2 $P 2>/dev/null || btrfs check --clear-space-cache v2 $P

CRO=$(btrfs inspect-internal dump-super $P | awk '/^compat_ro_flags/{print $2}')
INC=$(btrfs inspect-internal dump-super $P | awk '/^incompat_flags/{print $2}')
echo "== depois: compat_ro_flags=$CRO incompat_flags=$INC"

[ "$CRO" = 0x0 ] || { echo "ERRO: compat_ro ainda $CRO"; exit 1; }
if (( INC & 0x10 )); then
  echo "ATENÇÃO: bit do zstd (0x10) ligado. O kernel 4.4 não monta: regrave o cartão."
  exit 2
fi
echo "PRONTO. O sistema do cartão voltou a ser compatível."
