#!/usr/bin/env python3
"""inventario.py — lista as ROMs de uma partição de ROMs (ArkOS/dArkOS/EmuDeck) em JSON.

Uso: python3 inventario.py /caminho/da/pasta/roms > inv.json

Saída: {"<sistema>": [["caminho/relativo", tamanho_bytes, tem_save(0|1)], ...], ...}
Pula pastas que não são de jogos (bios, themes, tools...) e arquivos de save, mídia e config.
"""
import json
import os
import re
import sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
root = sys.argv[1]

SKIP_DIRS = {"bios", "themes", "tools", "launchimages", "backup", "System Volume Information",
             "videos", "movies", "bgmusic", "ports"}
NOT_GAME = re.compile(r"\.(txt|xml|png|jpe?g|srm|sav|state\d*|auto|mcd|mcr|cfg|ini|db|dat|nfo|bak)$", re.I)
SAVE = re.compile(r"\.(srm|sav|state\d*|mcd|mcr)$", re.I)
TRACK = re.compile(r"\(Track \d+\)|track\d+\.(bin|raw)$", re.I)

out = {}
for system in sorted(os.listdir(root)):
    path = os.path.join(root, system)
    if not os.path.isdir(path) or system in SKIP_DIRS:
        continue
    games, saves = [], set()
    for dirpath, _, files in os.walk(path):
        for f in files:
            rel = os.path.relpath(os.path.join(dirpath, f), path)
            if SAVE.search(f):
                saves.add(os.path.splitext(rel)[0])
                continue
            if NOT_GAME.search(f) or TRACK.search(f):
                continue
            try:
                size = os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                size = 0
            games.append((rel, size))
    if games:
        out[system] = [[rel, size, int(os.path.splitext(rel)[0] in saves)] for rel, size in games]

json.dump(out, sys.stdout, ensure_ascii=False, separators=(",", ":"))
