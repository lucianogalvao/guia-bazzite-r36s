#!/usr/bin/env python3
"""teste-cartao-falso.py — teste rápido de cartão falsificado. APAGA O CARTÃO.

Grava N blocos de 1 MiB, cada um marcado com o próprio endereço, espalhados por todo o espaço
anunciado. Depois relê tudo direto do dispositivo (O_DIRECT, sem cache). Um cartão falso
"dá a volta" no espaço real e sobrescreve blocos antigos, que voltam diferentes.

Uso: sudo python3 teste-cartao-falso.py /dev/sdX [N=512]
Antes, desmonte todas as partições do cartão.
"""
import hashlib
import mmap
import os
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
dev = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 512
BS = 1 << 20

fd = os.open(dev, os.O_RDWR | os.O_DIRECT | os.O_SYNC)
size = os.lseek(fd, 0, os.SEEK_END)
slots = size // BS - 1
offs = sorted({int(i * slots / (N - 1)) * BS for i in range(N)})
buf = mmap.mmap(-1, BS)  # alinhado à página, exigido pelo O_DIRECT


def pattern(off):
    seed = hashlib.sha256(b"bloco-%d" % off).digest()
    return seed * (BS // len(seed))


for o in offs:
    buf.seek(0)
    buf.write(pattern(o))
    os.pwritev(fd, [buf], o)
os.fsync(fd)

bad = []
for o in offs:
    n = os.preadv(fd, [buf], o)
    if n != BS or buf[:] != pattern(o):
        bad.append(o)
os.close(fd)

print(f"tamanho={size / 1e9:.2f} GB blocos={len(offs)} ruins={len(bad)}")
if bad:
    print(f"primeiro bloco ruim em {bad[0] / 1e9:.2f} GB, último em {bad[-1] / 1e9:.2f} GB")
    sys.exit(1)
