"""Ferramentas que o modelo pode chamar. Fora desta lista, ele não faz nada."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from . import acoes, config, diagnostico, gpu, r36s, roms
from .executor import Executor
from .propostas import Propostas


def _f(nome: str, descricao: str, props: dict | None = None, obrigatorios: list[str] | None = None) -> dict:
    return {"type": "function", "function": {
        "name": nome, "description": descricao,
        "parameters": {"type": "object", "properties": props or {}, "required": obrigatorios or []}}}


_STR_LISTA = {"type": "array", "items": {"type": "string"}}
LISTA = [
    _f("status", "Estado do PC: discos, Sunshine, jogo aberto, espaço livre, último backup."),
    _f("diagnosticar", "Procura problemas conhecidos (Sunshine, discos) e diz o que fazer."),
    _f("ler_log", "Últimas linhas do log de um serviço.",
       {"servico": {"type": "string", "enum": ["sunshine", "backup"]}, "linhas": {"type": "integer"}},
       ["servico"]),
    _f("reiniciar_sunshine", "Reinicia o Sunshine (resolve a maioria dos erros do Moonlight na TV)."),
    _f("listar_downloads", "Lista o que chegou em Downloads, o conteúdo dos compactados e o que ainda semeia."),
    _f("propor_organizacao", "Propõe extrair/mover ROMs para a pasta certa. A pessoa aprova na tela.",
       {"itens": {"type": "array", "items": {"type": "object", "properties": {
           "origem": {"type": "string"},
           "sistema": {"type": "string", "description": "pasta do sistema em Emulation/roms, ex.: snes, psx, switch"},
           "tipo": {"type": "string", "enum": ["base", "extra"], "description": "extra = update ou DLC do Switch"},
           "jogo": {"type": "string", "description": "nome do jogo, só para extras do Switch"}},
           "required": ["origem", "sistema", "tipo"]}}}, ["itens"]),
    _f("propor_apagar", "Propõe apagar arquivos de Downloads ou de switch-extras. Exige confirmação dupla.",
       {"caminhos": _STR_LISTA}, ["caminhos"]),
    _f("propor_fechar_jogo", "Propõe fechar o jogo ou emulador aberto (o que não foi salvo se perde). A pessoa aprova."),
    _f("r36s_info", "Mostra se o cartão do R36S está no leitor e quanto espaço tem."),
    _f("propor_copia_r36s", "Propõe copiar arquivos para uma pasta do cartão do R36S (ou 'bios').",
       {"arquivos": _STR_LISTA, "sistema": {"type": "string"}}, ["arquivos", "sistema"]),
    _f("propor_ejetar_r36s", "Propõe desmontar o cartão do R36S para tirar com segurança."),
]


def criar_registro(ex: Executor, propostas: Propostas,
                   ativos: Callable[[], set] = roms.torrents_ativos) -> tuple[list[dict], Callable[[str, dict], dict]]:

    def ler_log(servico: str, linhas: int = 60) -> dict:
        unit = {"sunshine": config.SUNSHINE_UNIT, "backup": config.BACKUP_UNIT}.get(servico)
        if not unit:
            raise ValueError("Serviço desconhecido. Use 'sunshine' ou 'backup'.")
        n = str(max(1, min(int(linhas), 200)))
        return {"log": ex.rodar(["journalctl", "--user", "-u", unit, "-n", n, "-o", "cat"]).saida}

    def diagnosticar() -> dict:
        itens = diagnostico.regras(diagnostico.coletar(ex))
        return {"itens": itens, "resumo": diagnostico.resumo(itens)}

    def propor(titulo: str, refazer: str, entrada: dict) -> dict:
        passos = refazedores[refazer](entrada)
        id_ = propostas.criar(titulo, passos, refazer=refazer, entrada=entrada)
        return {"proposta": id_, "passos": [p["descricao"] for p in passos]}

    def plano_apagar(entrada: dict) -> list[dict]:
        prot = ativos()
        passos = []
        for c in entrada["caminhos"]:
            p = Path(os.path.normpath(c))
            if p.is_symlink() or not (roms.dentro(p, config.DOWNLOADS) or roms.dentro(p, config.SWITCH_EXTRAS)):
                raise ValueError(f"Só apago dentro de Downloads ou switch-extras (sem atalhos): {c}")
            if roms.protegido(p, prot):
                raise ValueError(f"Esse arquivo ainda está semeando no qBittorrent: {c}")
            passos.append({"descricao": f"Apagar {p}", "args": ["rm", "--", str(p)], "apaga": True})
        return passos

    def plano_fechar(entrada: dict) -> list[dict]:
        j = gpu.jogo_aberto(ex)
        if not j:
            raise ValueError("Nenhum jogo aberto.")
        return [{"descricao": f"Fechar {j['nome']} (o que não foi salvo será perdido)",
                 "args": ["kill", "-TERM", str(j["pid"])], "apaga": False}]

    refazedores = {
        "fechar_jogo": plano_fechar,
        "organizar": lambda e: roms.planejar(e["itens"], ativos()),
        "apagar": plano_apagar,
        "r36s_copia": lambda e: r36s.planejar_copia(e["arquivos"], e["sistema"], r36s.detectar(ex)),
        "r36s_ejetar": lambda e: r36s.passos_ejetar(r36s.detectar(ex)),
    }
    propostas.refazedores.update(refazedores)

    funcs: dict[str, Callable[..., dict]] = {
        "status": lambda: acoes.status(ex),
        "diagnosticar": diagnosticar,
        "ler_log": ler_log,
        "reiniciar_sunshine": lambda: acoes.reiniciar_sunshine(ex),
        "listar_downloads": lambda: {"itens": roms.listar_downloads(ex, ativos=ativos())},
        "propor_organizacao": lambda itens: propor("Organizar Downloads", "organizar", {"itens": itens}),
        "propor_apagar": lambda caminhos: propor("Apagar arquivos", "apagar", {"caminhos": caminhos}),
        "propor_fechar_jogo": lambda: propor("Fechar o jogo", "fechar_jogo", {}),
        "r36s_info": lambda: r36s.detectar(ex),
        "propor_copia_r36s": lambda arquivos, sistema: propor(
            f"Copiar para o R36S ({sistema})", "r36s_copia", {"arquivos": arquivos, "sistema": sistema}),
        "propor_ejetar_r36s": lambda: propor("Ejetar o cartão do R36S", "r36s_ejetar", {}),
    }

    def chamar(nome: str, args: dict) -> dict:
        f = funcs.get(nome)
        if f is None:
            return {"erro": "Ferramenta não existe."}
        try:
            return f(**(args if isinstance(args, dict) else {}))
        except Exception as e:  # o modelo manda argumentos imprevisíveis; nunca derrubar a requisição
            return {"erro": str(e) or type(e).__name__}

    return LISTA, chamar
