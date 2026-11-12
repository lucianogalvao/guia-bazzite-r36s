#!/usr/bin/env python3
"""agrupar.py — agrupa o inventário por jogo, tira lixo e sugere uma versão por jogo.

Uso: python3 agrupar.py inv.json roms.json

Saída (roms.json): lista de sistemas ordenada por tamanho, cada um com:
  {"id", "name", "files", "bytes", "g": [ {"k": chave, "t": título, "s": tem_save,
     "j": todas_as_versões_são_protótipo/hack, "v": [[caminho, bytes, save, tags, lixo], ...]} ]}
A primeira versão de cada jogo ("v"[0]) é a sugerida: PT-BR > USA > World > Europa > Japão,
sem protótipos ou hacks, e sempre a que tem save.
"""
import collections
import json
import os
import re
import sys

if len(sys.argv) != 3:
    sys.exit(__doc__)
src = json.load(open(sys.argv[1]))

BAD_EXT = {".mp4", ".old", ".nv", ".hi", ".fs", ".glshadercache", ".sfo", ".ppst", ".rtc", "", ".xml", ".cfg", ".ini"}
BAD_DIR = re.compile(r"(^|/)(ppsspp|downloaded_videos|media|images|snap)(/|$)", re.I)
JUNK = re.compile(r"\b(proto|prototype|beta|demo|sample|hack|hacked|pirate|bootleg|unl|unlicensed|aftermarket|homebrew|test)\b"
                  r"|\[(b|h|t|f|o|p)\d*\]", re.I)
NAMES = {"alg": "American Laser Games", "atari5200": "Atari 5200", "atari7800": "Atari 7800",
         "cps1": "CPS-1 (Capcom)", "cps2": "CPS-2 (Capcom)", "cps3": "CPS-3 (Capcom)", "dreamcast": "Dreamcast",
         "easyrpg": "EasyRPG", "famicom": "Famicom", "gamegear": "Game Gear", "gb": "Game Boy",
         "gba": "Game Boy Advance", "gbc": "Game Boy Color", "mame2003": "Arcade (MAME 2003)",
         "megadrive": "Mega Drive", "n64": "Nintendo 64", "nds": "Nintendo DS", "neogeo": "Neo Geo", "nes": "NES",
         "pcengine": "PC Engine", "psp": "PSP", "psx": "PlayStation", "scummvm": "ScummVM", "sfc": "Super Famicom",
         "sg-1000": "SG-1000", "snes": "Super Nintendo", "wolf": "Wolfenstein 3D"}


def tags_of(rel):
    d, f = os.path.dirname(rel), os.path.basename(rel)
    out = [a or b for a, b in re.findall(r"\(([^)]*)\)|\[([^\]]*)\]", f)]
    if d:
        folder = re.sub(r"#+", "", d.split("/")[0]).strip()
        if folder and folder.lower() not in ("gb", "gbc", "."):
            out.insert(0, "dir:" + folder)
    return out


def title_of(rel):
    f = os.path.splitext(os.path.basename(rel))[0]
    f = re.sub(r"^\s*\d{1,4}[\s._-]+", "", f)  # "0001 Jogo" -> "Jogo"
    f = re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", f).strip(" ._-")
    return f or os.path.basename(rel)


def key_of(title):
    k = re.sub(r",\s*the\b", "", title.lower())
    k = re.sub(r"^the\s+", "", k).replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", k)


def score(rel, save):
    s, low = 0, rel.lower()
    if any(x in low for x in ("pt-br", "(brazil)", "t-por", "pt_br", "(pt")): s += 50
    if any(x in low for x in ("(usa", "(us)", "(u)")): s += 30
    if "(world" in low: s += 28
    if "(europe" in low or "(e)" in low: s += 20
    if "(japan" in low or "(j)" in low: s += 5
    if JUNK.search(os.path.basename(rel)): s -= 100
    m = re.search(r"\(rev\s*(\d+)\)", low)
    if m: s += int(m.group(1))
    if "[!]" in rel: s += 3
    if save: s += 500
    return s


out = []
for sysid, rows in src.items():
    groups = collections.OrderedDict()
    for rel, size, save in rows:
        if os.path.splitext(rel)[1].lower() in BAD_EXT or BAD_DIR.search(rel):
            continue
        t = title_of(rel)
        k = key_of(t) or ("f" + re.sub(r"[^A-Za-z0-9]", "", rel))[:60]
        groups.setdefault(k, []).append([rel, size, save, tags_of(rel), int(bool(JUNK.search(os.path.basename(rel))))])
    gl = []
    for k, v in groups.items():
        v.sort(key=lambda x: -score(x[0], x[2]))
        gl.append({"k": k, "t": title_of(v[0][0]), "v": v,
                   "s": int(any(x[2] for x in v)), "j": int(all(x[4] for x in v))})
    if not gl:
        continue
    gl.sort(key=lambda g: g["t"].lower())
    out.append({"id": sysid, "name": NAMES.get(sysid, sysid), "g": gl,
                "files": sum(len(g["v"]) for g in gl), "bytes": sum(x[1] for g in gl for x in g["v"])})

out.sort(key=lambda s: -s["bytes"])
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, separators=(",", ":"))
for s in out:
    print(f"{s['name']:24} {len(s['g']):5} jogos {s['files']:5} arquivos {s['bytes'] / 1e9:6.2f} GB "
          f"saves={sum(g['s'] for g in s['g'])} lixo={sum(g['j'] for g in s['g'])}")
