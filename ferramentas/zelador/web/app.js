"use strict";

const $ = (s) => document.querySelector(s);
const historico = [];
const SEM_CONEXAO = "Não consegui falar com o PC. Confira se ele está ligado e no Wi-Fi de casa.";

function el(tag, attrs = {}, ...filhos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else e.setAttribute(k, v);
  }
  for (const f of filhos) if (f != null) e.append(f);
  return e;
}

async function api(metodo, caminho, corpo) {
  const r = await fetch(caminho, {
    method: metodo,
    headers: corpo ? { "Content-Type": "application/json" } : {},
    body: corpo ? JSON.stringify(corpo) : undefined,
    credentials: "same-origin",
  });
  if (r.status === 401) { mostrarPin(); throw new Error("sem login"); }
  return { status: r.status, dados: await r.json().catch(() => ({})) };
}

// ---------- PIN ----------
function mostrarPin() { $("#tela-app").hidden = true; $("#tela-pin").hidden = false; $("#pin").focus(); }
function saudacao() {
  const h = new Date().getHours();
  return h < 5 ? "Boa madrugada" : h < 12 ? "Bom dia" : h < 18 ? "Boa tarde" : "Boa noite";
}

let primeiraPintura = true;
function mostrarApp() {
  $("#tela-pin").hidden = true; $("#tela-app").hidden = false;
  $("#saudacao").textContent = saudacao();
  atualizarEstado(); vigiarTarefas(); carregarPropostas(); carregarRegistro();
}

$("#form-pin").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  try {
    const r = await fetch("/api/login", { method: "POST", body: JSON.stringify({ pin: $("#pin").value }) });
    if (r.ok) { $("#pin").value = ""; $("#pin-erro").textContent = ""; mostrarApp(); }
    else $("#pin-erro").textContent = (await r.json().catch(() => ({}))).erro || "Não deu certo.";
  } catch { $("#pin-erro").textContent = SEM_CONEXAO; }
});

// ---------- Painel de status ----------
function gb(v) { return v == null ? "?" : `${Math.round(v)} GB livres`; }

function pintarPainel(s) {
  const discosOk = Object.values(s.discos || {}).every(Boolean);
  const sunshine = s.sunshine === "active";
  let classe = "anel-ok", frase = "Tudo pronto para jogar na TV";
  if (!sunshine) { classe = "anel-atencao"; frase = "O streaming está parado"; }
  if (!discosOk) { classe = "anel-perigo"; frase = "Um disco não montou"; }
  $("#anel").className = `anel ${classe}${primeiraPintura ? " acendendo" : ""}`;
  if (primeiraPintura) { primeiraPintura = false; setTimeout(() => $("#anel").classList.remove("acendendo"), 1000); }
  $("#frase").textContent = frase;

  const livre = s.livre_gb || {};
  const chips = [
    [s.jogo ? `Jogo aberto: ${s.jogo}` : "Nenhum jogo aberto", false],
    [`HD ${gb(livre["/var/mnt/roms"])}`, s.discos && !s.discos["/var/mnt/roms"]],
    [`NVMe ${gb(livre["/var/mnt/jogos"])}`, s.discos && !s.discos["/var/mnt/jogos"]],
  ];
  if (s.ultimo_backup) {
    const hora = (s.ultimo_backup.match(/\d{2}:\d{2}/) || [""])[0];
    chips.push([`Backup ${hora}`, false]);
  } else chips.push(["Sem backup dos saves", true]);
  $("#chips").replaceChildren(...chips.map(([t, alerta]) => el("li", alerta ? { class: "alerta" } : {}, t)));
  $("#btn-fechar").disabled = !s.jogo;
  $("#btn-fechar-texto").textContent = s.jogo ? `Fechar ${s.jogo}` : "Nenhum jogo aberto";
}

async function atualizarEstado() {
  try {
    const { dados } = await api("GET", "/api/status");
    pintarPainel(dados);
  } catch (e) {
    if (e.message !== "sem login") {
      $("#anel").className = "anel anel-perigo";
      $("#frase").textContent = "Sem contato com o PC";
      $("#chips").replaceChildren();
    }
  }
}

// ---------- Resultado dos botões ----------
function resultado(tipo, ...conteudo) {
  const r = $("#resultado");
  r.hidden = false;
  r.className = "aviso-caixa " + tipo;
  r.replaceChildren(...conteudo);
}

async function rodarAcao(nome, botao) {
  if (botao) botao.disabled = true;
  try {
    const { dados } = await api("POST", "/api/acao/" + nome);
    if (nome === "status") resultado("", tabelaStatus(dados));
    else resultado(dados.ok ? "ok" : "falha", dados.mensagem || "Feito.");
    atualizarEstado(); carregarRegistro();
  } catch (e) {
    if (e.message !== "sem login") resultado("falha", SEM_CONEXAO);
  } finally { if (botao) botao.disabled = false; }
}

function tabelaStatus(s) {
  const linhas = [
    ["Streaming", s.sunshine === "active" ? "rodando" : s.sunshine],
    ["Jogo aberto", s.jogo || "nenhum"],
    ...Object.entries(s.discos || {}).map(([d, ok]) =>
      [d, `${ok ? "montado" : "não montado"}${s.livre_gb && s.livre_gb[d] != null ? `, ${s.livre_gb[d]} GB livres` : ""}`]),
    ["Último backup", s.ultimo_backup || "nunca"],
  ];
  return el("dl", { class: "status" }, ...linhas.flatMap(([k, v]) => [el("dt", {}, k), el("dd", {}, v)]));
}

const NOMES_ACAO = { reiniciar_sunshine: "Reiniciar o streaming" };

$("#btn-diag").addEventListener("click", async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;
  try {
    const { dados } = await api("GET", "/api/diagnostico");
    const itens = dados.itens || [];
    const botoes = el("div", { class: "botoes" });
    for (const a of new Set(itens.map((i) => i.acao).filter(Boolean))) {
      botoes.append(el("button", { class: "botao botao-primario", onclick: (e) => rodarAcao(a, e.currentTarget) },
        NOMES_ACAO[a] || a));
    }
    botoes.append(el("button", { class: "botao", onclick: () => enviar(`Explique este diagnóstico e o que fazer: ${dados.resumo}`) },
      "Pedir explicação"));
    resultado(itens.length ? "atencao" : "ok", el("div", {}, dados.resumo), botoes);
  } catch (e) {
    if (e.message !== "sem login") resultado("falha", SEM_CONEXAO);
  } finally { b.disabled = false; }
});

$("#btn-fechar").addEventListener("click", async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;
  try {
    const { dados } = await api("POST", "/api/fechar_jogo", {});
    if (dados.erro) { resultado("falha", dados.erro); atualizarEstado(); }
    else resultado("atencao", cartaoProposta(dados.proposta));
  } catch (e) {
    if (e.message !== "sem login") resultado("falha", SEM_CONEXAO);
  } finally { b.disabled = false; }
});

$("#btn-desligar").addEventListener("click", async () => {
  let jogo = null;
  try { jogo = (await api("GET", "/api/status")).dados.jogo; } catch (e) { if (e.message === "sem login") return; }
  const aviso = jogo ? `O jogo ${jogo} está aberto e o que não foi salvo vai se perder.` : "Ninguém vai conseguir ligar de volta pelo celular.";
  const botoes = el("div", { class: "botoes" },
    el("button", { class: "botao botao-perigo", onclick: async (e) => {
      e.currentTarget.disabled = true;
      try {
        const { dados } = await api("POST", "/api/desligar", { confirmar: true });
        resultado(dados.ok ? "atencao" : "falha", dados.mensagem || dados.erro);
        carregarRegistro();
      } catch (e2) { if (e2.message !== "sem login") resultado("falha", SEM_CONEXAO); }
    } }, "Desligar agora"),
    el("button", { class: "botao", onclick: () => { $("#resultado").hidden = true; } }, "Cancelar"));
  resultado("atencao", el("div", {}, "Desligar o PC da sala? " + aviso), botoes);
  $("#resultado").scrollIntoView({ block: "center", behavior: "smooth" });
});

document.querySelectorAll("[data-acao]").forEach((b) =>
  b.addEventListener("click", () => rodarAcao(b.dataset.acao, b)));
document.querySelectorAll("[data-pedido]").forEach((b) =>
  b.addEventListener("click", () => enviar(b.dataset.pedido)));

// ---------- Tarefas ----------
let vigia = null;
async function vigiarTarefas() {
  clearTimeout(vigia);
  try {
    const { dados } = await api("GET", "/api/tarefas");
    const recentes = dados.filter((t) => t.situacao === "rodando" || Date.now() / 1000 - t.criada < 600);
    $("#tarefas").replaceChildren(...recentes.map(cartaoTarefa));
    if (dados.some((t) => t.situacao === "rodando")) vigia = setTimeout(vigiarTarefas, 3000);
  } catch { /* tenta de novo quando houver ação */ }
}

function cartaoTarefa(t) {
  const sit = { rodando: "em andamento", ok: "concluída", falhou: "falhou", interrompida: "interrompida" }[t.situacao];
  const pct = t.total ? Math.round((100 * t.passo) / t.total) : 100;
  const tipo = t.situacao === "ok" ? "ok" : t.situacao === "rodando" ? "" : "falha";
  const c = el("div", { class: `tarefa ${tipo}` },
    el("div", { class: "tarefa-topo" }, t.titulo, el("span", {}, `${sit} · ${t.passo}/${t.total}`)),
    el("div", { class: "barra" }, el("div", { style: `width:${pct}%` })));
  if (t.situacao === "falhou" && t.log_fim) c.append(el("pre", {}, t.log_fim));
  return c;
}

// ---------- Conversa ----------
function limparVazio() { const v = $("#mensagens .vazio"); if (v) v.remove(); }

function adicionarMsg(role, texto) {
  limparVazio();
  $("#mensagens").append(el("div", { class: `msg ${role}` }, texto));
  $("#mensagens").lastChild.scrollIntoView({ block: "end", behavior: "smooth" });
}

async function enviar(texto, forcar = false) {
  texto = (texto || "").trim();
  if (!texto) return;
  limparVazio();
  if (!forcar) { historico.push({ role: "user", content: texto }); adicionarMsg("user", texto); }
  const esperando = el("div", { class: "msg assistant pensando" }, "Deixa eu ver");
  $("#mensagens").append(esperando);
  esperando.scrollIntoView({ block: "end", behavior: "smooth" });
  try {
    const { dados } = await api("POST", "/api/chat", { historico, forcar });
    esperando.remove();
    if (dados.aviso) {
      const c = el("div", { class: "proposta" }, el("strong", {}, "Tem um jogo aberto"), dados.aviso,
        el("div", { class: "botoes" },
          el("button", { class: "botao botao-primario", onclick: (e) => { e.currentTarget.closest(".proposta").remove(); enviar(texto, true); } }, "Enviar mesmo assim"),
          el("button", { class: "botao", onclick: (e) => e.currentTarget.closest(".proposta").remove() }, "Cancelar")));
      $("#mensagens").append(c);
      return;
    }
    historico.push({ role: "assistant", content: dados.texto });
    carregarRegistro();
    adicionarMsg("assistant", dados.texto);
    for (const p of dados.propostas || []) if (!propostasNaTela.has(p.id)) $("#mensagens").append(cartaoProposta(p));
  } catch (e) {
    esperando.remove();
    if (e.message !== "sem login") adicionarMsg("assistant", SEM_CONEXAO);
  }
}

// Propostas criadas por um chat cuja resposta se perdeu (página fechada) reaparecem aqui.
const propostasNaTela = new Set();
async function carregarPropostas() {
  try {
    const { dados } = await api("GET", "/api/propostas");
    for (const p of dados) if (!propostasNaTela.has(p.id)) { limparVazio(); $("#mensagens").append(cartaoProposta(p)); }
  } catch { /* tenta de novo ao reabrir */ }
}

function cartaoProposta(p) {
  propostasNaTela.add(p.id);
  const apaga = p.passos.some((x) => x.apaga);
  const botoes = el("div", { class: "botoes" });
  const c = el("div", { class: `proposta${apaga ? " apaga" : ""}` },
    el("strong", {}, p.titulo),
    el("ol", {}, ...p.passos.map((x) => el("li", {}, x.descricao))),
    botoes);

  const aprovar = el("button", { class: `botao ${apaga ? "botao-perigo" : "botao-primario"}` },
    apaga ? "Aprovar e apagar" : "Aprovar");
  const recusar = el("button", { class: "botao" }, "Recusar");

  async function pedir(corpo) {
    try { return (await api("POST", `/api/aprovar/${p.id}`, corpo)).dados; }
    catch (e) { return { ok: false, mensagem: e.message === "sem login" ? "Entre com o PIN de novo." : SEM_CONEXAO }; }
  }
  aprovar.addEventListener("click", async () => {
    aprovar.disabled = recusar.disabled = true;
    const dados = await pedir({});
    if (dados.precisa_confirmar_apagar) {
      const sim = el("button", { class: "botao botao-perigo" }, "Sim, apagar");
      botoes.replaceChildren(el("span", {}, "Tem certeza? Não dá para desfazer."), sim,
        el("button", { class: "botao", onclick: () => fechar("Cancelado.") }, "Não"));
      sim.addEventListener("click", async () => {
        sim.disabled = true;
        const d = await pedir({ confirmar_apagar: true });
        fechar(d.ok ? "Aprovado. O andamento aparece acima." : d.mensagem);
      });
      return;
    }
    fechar(dados.ok ? "Aprovado. O andamento aparece acima." : dados.mensagem);
  });
  recusar.addEventListener("click", async () => {
    recusar.disabled = aprovar.disabled = true;
    try { await api("POST", `/api/recusar/${p.id}`, {}); fechar("Recusado."); }
    catch { fechar(SEM_CONEXAO); }
  });
  function fechar(msg) {
    botoes.replaceChildren(el("span", { class: "sutil" }, msg));
    vigiarTarefas(); carregarRegistro();
    setTimeout(() => { atualizarEstado(); carregarRegistro(); }, 2500);
  }
  botoes.append(aprovar, recusar);
  return c;
}

const caixa = $("#texto");
caixa.addEventListener("input", () => { caixa.style.height = "auto"; caixa.style.height = caixa.scrollHeight + "px"; });
caixa.addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey && !ev.isComposing) { ev.preventDefault(); $("#form-chat").requestSubmit(); }
});
$("#form-chat").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const t = caixa.value;
  caixa.value = ""; caixa.style.height = "auto";
  enviar(t);
});

// Ao voltar para o app (iPhone), atualiza o painel, as tarefas e as propostas.
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && !$("#tela-app").hidden) { atualizarEstado(); vigiarTarefas(); carregarPropostas(); carregarRegistro(); }
});

// ---------- Registro ----------
const NOMES_TIPO = { acao: "Botão", chat: "Conversa", proposta: "Proposta", tarefa: "Tarefa",
  login: "Entrada", diagnostico: "Diagnóstico" };
let registroItens = [], registroMostrando = 40;

function diaLegivel(d) {
  const hoje = new Date(); const ontem = new Date(Date.now() - 864e5);
  const iso = (x) => x.toLocaleDateString("sv-SE");
  if (d === iso(hoje)) return "Hoje";
  if (d === iso(ontem)) return "Ontem";
  const [a, m, dd] = d.split("-");
  return `${dd}/${m}/${a}`;
}

function desenharRegistro() {
  const lista = $("#registro-lista");
  if (!registroItens.length) { lista.replaceChildren(el("p", { class: "vazio" }, "Nada registrado ainda.")); }
  else {
    const nos = []; let diaAtual = null;
    for (const i of registroItens.slice(0, registroMostrando)) {
      const [dia, hora] = i.quando.split(" ");
      if (dia !== diaAtual) { diaAtual = dia; nos.push(el("div", { class: "registro-dia" }, diaLegivel(dia))); }
      const erro = /errado|falhou|Barrada|não voltou|Não consegui/.test(i.texto);
      nos.push(el("div", { class: `registro-item${erro ? " erro-item" : ""}` },
        el("time", {}, hora.slice(0, 5)),
        el("span", { class: `registro-tipo t-${i.tipo}` }, NOMES_TIPO[i.tipo] || i.tipo),
        el("p", {}, i.texto)));
    }
    lista.replaceChildren(...nos);
  }
  $("#btn-registro-mais").hidden = registroItens.length <= registroMostrando;
}

async function carregarRegistro() {
  try {
    const { dados } = await api("GET", "/api/registro");
    registroItens = Array.isArray(dados) ? dados : [];
    desenharRegistro();
  } catch { /* sem login ou offline */ }
}
$("#btn-registro").addEventListener("click", carregarRegistro);
$("#btn-registro-mais").addEventListener("click", () => { registroMostrando += 40; desenharRegistro(); });

// ---------- Início ----------
api("GET", "/api/status").then(mostrarApp).catch(() => {});
