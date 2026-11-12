#!/usr/bin/bash
# comparar-dtb.sh — ordena as variantes do dArkOSRE pela semelhança com o .dtb de fábrica.
#
# Uso: comparar-dtb.sh <dtb-de-fabrica> <pasta-dtb-do-darkosre>
#   ex.: comparar-dtb.sh rk3326-r35s-linux.dtb /mnt/darkos/dtb
# Precisa do dtc (brew install dtc). Colunas: linhas diferentes no bloco do painel,
# linhas diferentes no arquivo todo, variante. Quanto menor, mais parecido.
set -euo pipefail
F=${1:?dtb de fábrica}; D=${2:?pasta dtb do dArkOSRE}

dts() { dtc -I dtb -O dts -q "$1" 2>/dev/null | grep -v phandle; }
panel() {
  # Lê até o fim (sem "exit" no awk), senão o pipefail aborta o script com SIGPIPE no dtc.
  dts "$1" | awk '/panel@0 \{/ && !done {f=1;d=0} f{print; d+=gsub(/\{/,"{"); d-=gsub(/\}/,"}"); if(d<=0 && /\};/){f=0;done=1}}' \
    | { grep -vE "reset-gpios|enable-gpios|backlight" || true; }
}

FP=$(mktemp); FA=$(mktemp); trap 'rm -f "$FP" "$FA"' EXIT
panel "$F" > "$FP"; dts "$F" > "$FA"

find "$D" -name rk3326-r36s-linux.dtb | sort | while read -r c; do
  p=$(diff "$FP" <(panel "$c") | grep -c '^[<>]' || true)
  a=$(diff "$FA" <(dts "$c") | grep -c '^[<>]' || true)
  printf '%4s %5s  %s\n' "$p" "$a" "$(dirname "${c#$D/}")"
done | sort -n

echo
echo "Para ver o que muda nas finalistas:"
echo "  diff <(dtc -I dtb -O dts -q $F) <(dtc -I dtb -O dts -q \"$D/<tipo>/<variante>/rk3326-r36s-linux.dtb\") | grep -E 'porch|sync-len|gpios|code|init-sequence'"
