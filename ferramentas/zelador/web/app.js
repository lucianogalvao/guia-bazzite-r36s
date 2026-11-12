"use strict";

const $ = (s) => document.querySelector(s);
const historico = [];

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
function mostrarApp() { $("#tela-pin").hidden = true; $("#tela-app").hidden = false; atualizarEstado(); vigiarTarefas(); }

$("#form-pin").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const r = await fetch("/api/login", { method: "POST", body: JSON.stringify({ pin: $("#pin").value }) });
  if (r.ok) { $("#pin").value = ""; $("#pin-erro").textContent = ""; mostrarApp(); }
  else $("#pin-erro").textContent = (await r.json().catch(() => ({}))).erro || "Não deu certo.";
});

// ---------- Resultado dos botões ----------
function resultado(tipo, ...conteudo) {
  const r = $("#resultado");
  r.hidden = false;
  r.className = "cartao " + tipo;
  r.replaceChildren(...conteudo);
}

async function rodarAcao(nome, botao) {
  if (botao) botao.disabled = true;
  try {
    const { dados } = await api("POST", "/api/acao/" + nome);
    if (nome === "status") resultado("", textoStatus(dados));
    else resultado(dados.ok ? "ok" : "falha", dados.mensagem || "Feito.");
    atualizarEstado();
  } catch (e) {
    if (e.message !== "sem login") resultado("falha", "Não consegui falar com o PC.");
  } finally { if (botao) botao.disabled = false; }
}

function textoStatus(s) {
  const linhas = [
    `Sunshine: ${s.sunshine === "active" ? "rodando" : s.sunshine}`,
    `Jogo aberto: ${s.jogo || "nenhum"}`,
    ...Object.entries(s.discos || {}).map(([d, ok]) =>
      `${d}: ${ok ? "montado" : "NÃO montado"}${s.livre_gb && s.livre_gb[d] != null ? `, ${s.livre_gb[d]} GB livres` : ""}`),
    `Último backup dos saves: ${s.ultimo_backup || "nunca"}`,
  ];
  return el("pre", {}, linhas.join("\n"));
}

const NOMES_ACAO = { reiniciar_sunshine: "Reiniciar Sunshine" };

$("#btn-diag").addEventListener("click", async (ev) => {
  const b = ev.currentTarget;
  b.disabled = true;
  try {
    const { dados } = await api("GET", "/api/diagnostico");
    const itens = dados.itens || [];
    const botoes = el("div", { class: "botoes" });
    for (const a of new Set(itens.map((i) => i.acao).filter(Boolean))) {
      botoes.append(el("button", { class: "primario", onclick: (e) => rodarAcao(a, e.currentTarget) }, NOMES_ACAO[a] || a));
    }
    botoes.append(el("button", { onclick: () => enviar(`Explique este diagnóstico e o que fazer: ${dados.resumo}`) },
      "Pedir explicação"));
    resultado(itens.length ? "aviso" : "ok", el("div", {}, dados.resumo), botoes);
  } catch (e) {
    if (e.message !== "sem login") resultado("falha", "Não consegui falar com o PC.");
  } finally { b.disabled = false; }
});

document.querySelectorAll("[data-acao]").forEach((b) =>
  b.addEventListener("click", () => rodarAcao(b.dataset.acao, b)));
document.querySelectorAll("[data-pedido]").forEach((b) =>
  b.addEventListener("click", () => enviar(b.dataset.pedido)));

async function atualizarEstado() {
  try {
    const { dados } = await api("GET", "/api/status");
    $("#estado-pc").textContent = dados.sunshine === "active" ? "Sunshine rodando" : "Sunshine parado";
  } catch { /* sem login ou offline */ }
}

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
  const barra = el("div", { class: "barra" }, el("div", { style: `width:${pct}%` }));
  const c = el("div", { class: `cartao tarefa ${tipo}` }, el("strong", {}, t.titulo), ` · ${sit} (${t.passo}/${t.total})`, barra);
  if (t.situacao === "falhou" && t.log_fim) c.append(el("pre", {}, t.log_fim));
  return c;
}

// ---------- Chat ----------
function adicionarMsg(role, texto) {
  $("#mensagens").append(el("div", { class: `msg ${role}` }, texto));
  $("#mensagens").lastChild.scrollIntoView({ block: "end", behavior: "smooth" });
}

async function enviar(texto, forcar = false) {
  texto = (texto || "").trim();
  if (!texto) return;
  if (!forcar) { historico.push({ role: "user", content: texto }); adicionarMsg("user", texto); }
  const esperando = el("div", { class: "msg assistant" }, "Pensando…");
  $("#mensagens").append(esperando);
  try {
    const { dados } = await api("POST", "/api/chat", { historico, forcar });
    esperando.remove();
    if (dados.aviso) {
      const c = el("div", { class: "cartao aviso" }, dados.aviso,
        el("div", { class: "botoes" },
          el("button", { class: "primario", onclick: (e) => { e.currentTarget.closest(".cartao").remove(); enviar(texto, true); } }, "Enviar mesmo assim"),
          el("button", { onclick: (e) => e.currentTarget.closest(".cartao").remove() }, "Cancelar")));
      $("#mensagens").append(c);
      return;
    }
    historico.push({ role: "assistant", content: dados.texto });
    adicionarMsg("assistant", dados.texto);
    for (const p of dados.propostas || []) $("#mensagens").append(cartaoProposta(p));
  } catch (e) {
    esperando.remove();
    if (e.message !== "sem login") adicionarMsg("assistant", "Não consegui falar com o PC.");
  }
}

function cartaoProposta(p) {
  const apaga = p.passos.some((x) => x.apaga);
  const lista = el("ul", {}, ...p.passos.map((x) => el("li", {}, x.descricao)));
  const botoes = el("div", { class: "botoes" });
  const c = el("div", { class: "cartao aviso" }, el("strong", {}, p.titulo), lista, botoes);

  const aprovar = el("button", { class: apaga ? "perigo" : "primario" }, apaga ? "Aprovar (apaga arquivos)" : "Aprovar");
  const recusar = el("button", {}, "Recusar");
  aprovar.addEventListener("click", async () => {
    aprovar.disabled = recusar.disabled = true;
    let { dados } = await api("POST", `/api/aprovar/${p.id}`, {});
    if (dados.precisa_confirmar_apagar) {
      const sim = el("button", { class: "perigo" }, "Sim, apagar");
      botoes.replaceChildren(el("span", {}, "Tem certeza? Não dá para desfazer."), sim,
        el("button", { onclick: () => fechar("Cancelado.") }, "Não"));
      sim.addEventListener("click", async () => {
        sim.disabled = true;
        ({ dados } = await api("POST", `/api/aprovar/${p.id}`, { confirmar_apagar: true }));
        fechar(dados.ok ? "Aprovado. Acompanhe acima." : dados.mensagem);
      });
      return;
    }
    fechar(dados.ok ? "Aprovado. Acompanhe acima." : dados.mensagem);
  });
  recusar.addEventListener("click", async () => {
    recusar.disabled = aprovar.disabled = true;
    await api("POST", `/api/recusar/${p.id}`, {});
    fechar("Recusado.");
  });
  function fechar(msg) {
    botoes.replaceChildren(el("span", { class: "sutil" }, msg));
    c.className = "cartao";
    vigiarTarefas();
  }
  botoes.append(aprovar, recusar);
  return c;
}

$("#form-chat").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const t = $("#texto").value;
  $("#texto").value = "";
  enviar(t);
});

// ---------- Início ----------
api("GET", "/api/status").then(mostrarApp).catch(() => {});
