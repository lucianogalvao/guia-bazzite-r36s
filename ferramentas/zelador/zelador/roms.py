"""ROMs: o que chegou em Downloads, o que ainda semeia e o plano para organizar."""
from __future__ import annotations

import re
from pathlib import Path

from . import config
from .executor import Executor

COMPACTADOS = {".7z", ".zip", ".rar"}
LIXO_EXT = {".nfo", ".html", ".jpg", ".jpeg", ".png", ".webp", ".txt"}
LIXO_NOMES = {"metadata.json"}


# ---- bencode mínimo (só o necessário para ler .fastresume) ----
def _bdecode(d: bytes, i: int = 0):
    c = d[i:i + 1]
    if c == b"i":
        f = d.index(b"e", i)
        return int(d[i + 1:f]), f + 1
    if c in (b"l", b"d"):
        i += 1
        itens = []
        while d[i:i + 1] != b"e":
            v, i = _bdecode(d, i)
            itens.append(v)
        if c == b"l":
            return itens, i + 1
        return dict(zip(itens[::2], itens[1::2])), i + 1
    sep = d.index(b":", i)
    n = int(d[i:sep])
    return d[sep + 1:sep + 1 + n], sep + 1 + n


def torrents_ativos(dir_backup: Path | None = None) -> set[Path]:
    dir_backup = Path(dir_backup or config.QBT_BACKUP)
    ativos = set()
    if not dir_backup.is_dir():
        return ativos
    for f in dir_backup.glob("*.fastresume"):
        try:
            d, _ = _bdecode(f.read_bytes())
        except (ValueError, IndexError):
            continue
        nome = d.get(b"name") or d.get(b"qBt-name")
        base = d.get(b"save_path") or d.get(b"qBt-savePath")
        if nome and base:
            ativos.add(Path(base.decode(errors="replace")) / nome.decode(errors="replace"))
    return ativos


def protegido(caminho: Path, ativos: set[Path]) -> bool:
    caminho = Path(caminho)
    return any(caminho == a or a in caminho.parents for a in ativos)


def listar_downloads(ex: Executor, raiz: Path | None = None, ativos: set[Path] | None = None) -> list[dict]:
    raiz = Path(raiz or config.DOWNLOADS)
    ativos = torrents_ativos() if ativos is None else ativos
    itens = []
    for f in sorted(raiz.rglob("*")):
        if not f.is_file() or f.name in LIXO_NOMES or f.suffix.lower() in LIXO_EXT or f.name.startswith("BLUEROMS"):
            continue
        tam = f.stat().st_size
        if tam < 5 * 2**20:
            continue
        conteudo = []
        if f.suffix.lower() in COMPACTADOS:
            r = ex.rodar(["7z", "l", "-ba", "-slt", str(f)], timeout=60)
            conteudo = [l[len("Path = "):] for l in r.saida.splitlines() if l.startswith("Path = ")]
        itens.append({"caminho": str(f), "mib": tam // 2**20, "conteudo": conteudo,
                      "protegido": protegido(f, ativos)})
    return itens


def _titulo(nome: str) -> str:
    return re.sub(r"\s*[\(\[][^\)\]]*[\)\]]", "", nome).strip() or nome


def planejar(itens: list[dict], ativos: set[Path] | None = None) -> list[dict]:
    """Cada item: {"origem", "sistema", "tipo": "base"|"extra", "jogo"?}. Nunca gera passo que apaga."""
    ativos = ativos or set()
    passos = []
    for it in itens:
        origem = Path(it["origem"])
        sistema, tipo = it["sistema"], it.get("tipo", "base")
        if sistema == "switch" and tipo == "extra":
            destino = Path(config.SWITCH_EXTRAS) / (it.get("jogo") or _titulo(origem.parent.name))
            passos.append({"descricao": f"Criar pasta {destino}", "args": ["mkdir", "-p", str(destino)],
                           "apaga": False})
        elif sistema == "switch":
            destino = Path(config.SWITCH)
        else:
            destino = Path(config.ROMS) / sistema
            if not destino.is_dir():
                raise ValueError(f"Pasta do sistema '{sistema}' não existe em {config.ROMS}.")
        if origem.suffix.lower() in COMPACTADOS:
            passos.append({"descricao": f"Extrair {origem.name} para {destino}",
                           "args": ["7z", "x", "-y", "-aos", f"-o{destino}", str(origem)], "apaga": False})
        elif protegido(origem, ativos):
            passos.append({"descricao": f"Copiar {origem.name} para {destino} (torrent ainda semeando)",
                           "args": ["cp", "-n", str(origem), str(destino / origem.name)], "apaga": False})
        else:
            passos.append({"descricao": f"Mover {origem.name} para {destino}",
                           "args": ["mv", "-n", str(origem), str(destino / origem.name)], "apaga": False})
    return passos
