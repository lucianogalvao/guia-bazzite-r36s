#!/usr/bin/bash
# regravar-cartao.sh — grava o dArkOSRE num cartão do R36S, confere e instala a variante.
#
# Uso:  sudo IMG=/caminho/dArkOSRE.img SHA=<sha1-do-img> DTB="dtb/soysauce/<variante>" bash regravar-cartao.sh
#
# Acha o cartão pelo rótulo ROOTFS (cartão já com dArkOSRE) ou pelo DEV informado (cartão novo):
#   sudo DEV=/dev/sdX IMG=... SHA=... DTB=... bash regravar-cartao.sh
# Só age em disco USB removível com menos de 70 GB. Instala também a regra que impede o PC de
# montar o ROOTFS (veja docs/r36s/01-antes-de-tudo.md).
set -euo pipefail

IMG=${IMG:?defina IMG=/caminho/da/imagem.img}
SHA=${SHA:?defina SHA=<sha1 do .img publicado na release>}
DTB=${DTB:?defina DTB=\"dtb/<tipo>/<variante>\"}
RULE_SRC=${RULE_SRC:-"$(dirname "$0")/../../config/r36s/98-r36s-no-automount.rules"}

[ "$(id -u)" = 0 ] || { echo "Rode com sudo"; exit 1; }
[ -f "$IMG" ] || { echo "Imagem não encontrada: $IMG"; exit 1; }

echo "== 1/6 Regra para o PC não montar o ROOTFS do cartão"
install -m644 "$RULE_SRC" /etc/udev/rules.d/98-r36s-no-automount.rules
udevadm control --reload

echo "== 2/6 Identificando o cartão"
if [ -z "${DEV:-}" ]; then
  DEV=/dev/$(lsblk -no PKNAME /dev/disk/by-label/ROOTFS | head -1)
fi
TRAN=$(lsblk -dno TRAN "$DEV"); RM=$(lsblk -dno RM "$DEV" | tr -d ' '); SIZE=$(blockdev --getsize64 "$DEV")
echo "   $DEV  tran=$TRAN removível=$RM tamanho=$((SIZE/1000000000)) GB"
[ "$TRAN" = usb ] && [ "$RM" = 1 ] && [ "$SIZE" -lt 70000000000 ] \
  || { echo "ABORTADO: $DEV não parece um cartão no leitor USB"; exit 1; }

echo "== 3/6 Desmontando"
for p in $(lsblk -lnpo NAME "$DEV" | tail -n +2); do umount "$p" 2>/dev/null || true; done
lsblk -no MOUNTPOINTS "$DEV" | grep -q . && { echo "ABORTADO: ainda montado"; exit 1; }

echo "== 4/6 Gravando"
dd if="$IMG" of="$DEV" bs=4M conv=fsync oflag=direct status=progress

echo "== 5/6 Conferindo a gravação (relendo o cartão)"
sync; echo 3 > /proc/sys/vm/drop_caches
GOT=$(head -c "$(stat -c %s "$IMG")" "$DEV" | sha1sum | cut -d' ' -f1)
[ "$GOT" = "$SHA" ] && echo "   SHA1 OK" || { echo "ERRO: SHA1 $GOT diferente de $SHA"; exit 1; }

echo "== 6/6 Instalando a variante $DTB"
partprobe "$DEV"; sleep 3
M=$(mktemp -d); mount "${DEV}1" "$M"
[ -d "$M/$DTB" ] || { umount "$M"; echo "ERRO: $DTB não existe na partição BOOT"; exit 1; }
rm -f "$M"/*.dtb; cp "$M/$DTB"/* "$M"/; sync
ls -1 "$M"/*.dtb
umount "$M"; rmdir "$M"; sync; eject "$DEV" || true

echo; echo "PRONTO. Primeiro boot no R36S: slot TF1, sem carregador, até o menu com música."
