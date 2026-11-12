"""Cartão do R36S no leitor USB do PC. Só se escreve na EASYROMS; o ROOTFS (btrfs) nunca é montado.

Ver docs/r36s/01-antes-de-tudo.md: montar o ROOTFS no Bazzite estraga o boot do R36S.
"""
from __future__ import annotations

import json
from pathlib import Path

from .executor import Executor


def _particoes(dev: dict):
    for f in dev.get("children") or []:
        yield f
        yield from _particoes(f)


def detectar(ex: Executor) -> dict:
    info = {"presente": False, "easyroms": None, "boot": None, "rootfs_montado": False, "livre_gb": None}
    r = ex.rodar(["lsblk", "-J", "-o", "NAME,LABEL,FSTYPE,MOUNTPOINT,TRAN"])
    if r.codigo != 0:
        return info
    for disco in json.loads(r.saida).get("blockdevices", []):
        if disco.get("tran") != "usb":
            continue
        parts = {p.get("label"): p for p in _particoes(disco)}
        if "EASYROMS" not in parts:
            continue
        info["presente"] = True
        info["easyroms"] = parts["EASYROMS"].get("mountpoint")
        info["boot"] = (parts.get("BOOT") or {}).get("mountpoint")
        info["rootfs_montado"] = bool((parts.get("ROOTFS") or {}).get("mountpoint"))
        if info["easyroms"]:
            d = ex.rodar(["df", "-B1", "--output=avail", info["easyroms"]]).saida.split()
            if d and d[-1].isdigit():
                info["livre_gb"] = round(int(d[-1]) / 2**30, 1)
        break
    return info


def _validar(info: dict) -> str:
    if not info.get("presente"):
        raise ValueError("Cartão do R36S não encontrado.")
    if info.get("rootfs_montado"):
        raise ValueError("A partição de sistema (ROOTFS) do cartão está montada. "
                         "Desmonte antes: isso pode estragar o R36S.")
    if not info.get("easyroms"):
        raise ValueError("A partição EASYROMS do cartão não está montada.")
    return info["easyroms"]


def planejar_copia(arquivos: list[str], sistema: str, info: dict) -> list[dict]:
    base = _validar(info)
    if not (Path(base) / sistema).is_dir():
        raise ValueError(f"Pasta {sistema} não existe no cartão.")
    destino = f"{base}/{sistema}/"
    return [{"descricao": f"Copiar {a} para o R36S ({sistema})", "args": ["cp", "-n", "--", a, destino],
             "apaga": False} for a in arquivos]


def passos_ejetar(info: dict) -> list[dict]:
    base = _validar(info)
    passos = [{"descricao": "Gravar o que falta no cartão", "args": ["sync"], "apaga": False},
              {"descricao": "Desmontar EASYROMS", "args": ["umount", base], "apaga": False}]
    if info.get("boot"):
        passos.append({"descricao": "Desmontar BOOT", "args": ["umount", info["boot"]], "apaga": False})
    return passos
