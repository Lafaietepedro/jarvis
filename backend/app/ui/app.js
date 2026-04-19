const state = {
  loading: false,
  refreshTimer: null,
  memoryAuditFilters: null,
};

const nodes = {
  title: document.querySelector("#status-title"),
  greeting: document.querySelector("#greeting"),
  statePill: document.querySelector("#state-pill"),
  presenceList: document.querySelector("#presence-list"),
  privacyList: document.querySelector("#privacy-list"),
  checkpointList: document.querySelector("#checkpoint-list"),
  checkpointEvents: document.querySelector("#checkpoint-events"),
  historyList: document.querySelector("#history-list"),
  memoryAuditForm: document.querySelector("#memory-audit-form"),
  memoryAuditIntent: document.querySelector("#memory-audit-intent"),
  memoryAuditSkill: document.querySelector("#memory-audit-skill"),
  memoryAuditAction: document.querySelector("#memory-audit-action"),
  memoryAuditSince: document.querySelector("#memory-audit-since"),
  memoryAuditUntil: document.querySelector("#memory-audit-until"),
  memoryAuditLimit: document.querySelector("#memory-audit-limit"),
  memoryAuditClear: document.querySelector("#memory-audit-clear"),
  memoryAuditDeleteFiltered: document.querySelector("#memory-audit-delete-filtered"),
  memoryAuditList: document.querySelector("#memory-audit-list"),
  memoryAuditSample: document.querySelector("#memory-audit-sample"),
  nextActions: document.querySelector("#next-actions"),
  refreshInterval: document.querySelector("#refresh-interval"),
  form: document.querySelector("#command-form"),
  input: document.querySelector("#command-input"),
  confirm: document.querySelector("#confirm-actions"),
  private: document.querySelector("#private-command"),
  lastResponse: document.querySelector("#last-response"),
  pauseButton: document.querySelector("#pause-button"),
  resumeButton: document.querySelector("#resume-button"),
  refreshButton: document.querySelector("#refresh-button"),
};

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options,
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function loadState() {
  if (state.loading) return;
  state.loading = true;
  try {
    const payload = await requestJson("/ui/state?history_limit=6");
    renderState(payload);
    if (state.memoryAuditFilters) {
      await loadMemoryAudit(state.memoryAuditFilters, false);
    }
  } catch (error) {
    nodes.lastResponse.textContent = `Nao consegui sincronizar: ${error.message}`;
    nodes.lastResponse.classList.add("error");
    nodes.statePill.textContent = "offline";
    nodes.statePill.className = "state-pill";
  } finally {
    state.loading = false;
  }
}

function renderState(payload) {
  const presence = payload.presence || {};
  const project = presence.project || {};
  const checkpoints = payload.checkpoints || {};
  const privacy = payload.privacy || {};
  const permissions = privacy.permissions || {};
  const memory = privacy.memory || {};
  const summary = checkpoints.summary || {};
  const capabilities = payload.capabilities || {};
  const proactive = payload.proactive || {};
  const memoryAudit = payload.memory_audit || {};

  nodes.title.textContent = `${presence.name || "JARVIS"} - ${presence.status || "unknown"}`;
  nodes.greeting.textContent = presence.greeting || "Estado local indisponivel.";
  nodes.statePill.textContent = presence.status || "unknown";
  nodes.statePill.className = `state-pill ${presence.status || ""}`;
  nodes.lastResponse.classList.remove("error");

  renderDefinitionList(nodes.presenceList, [
    ["Projeto", `${project.name || "unknown"} (${project.path || "unknown"})`],
    ["Voz", presence.voice_listening ? "ouvindo" : "em espera"],
    ["Tarefa", presence.current_task || "nenhuma"],
    ["Uptime", `${presence.uptime_seconds || 0}s`],
    ["Checkpoints", String(checkpoints.pending_count || 0)],
    ["Proximo passo", summary.next_step || "nenhum"],
    ["Arquivos", String(((capabilities.state || {}).files || {}).tracked_count || 0)],
    ["Sugestoes proativas", String((proactive.suggestions || []).length)],
  ]);

  renderDefinitionList(nodes.privacyList, [
    ["Nuvem", permissions.cloud_enabled ? "ativa" : "desligada"],
    ["Memoria", memory.enabled ? "ativa" : "desligada"],
    ["Comandos", String(memory.commands_recorded || 0)],
    ["Auditados", String(memoryAudit.matching_count || 0)],
    ["Shell", permissions.shell_enabled ? "permitido" : "bloqueado"],
    ["IDE", permissions.ide_actions_enabled ? "permitida" : "bloqueada"],
    ["Midia", permissions.media_actions_enabled ? "permitida" : "bloqueada"],
    ["Comandos", String((capabilities.commands || {}).count || 0)],
    ["Ações bloqueadas", String(capabilities.blocked_count || 0)],
  ]);

  renderCheckpoints(checkpoints.checkpoints || []);
  renderCheckpointEvents(checkpoints.events || []);
  renderHistory((payload.history || {}).commands || []);
  renderMemoryAudit(memoryAudit);
  renderNextActions(payload.actions || payload.next_actions || []);
}

function renderDefinitionList(target, items) {
  target.replaceChildren();
  for (const [label, value] of items) {
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    target.append(term, description);
  }
}

function renderCheckpoints(checkpoints) {
  nodes.checkpointList.replaceChildren();
  if (!checkpoints.length) {
    nodes.checkpointList.append(emptyText("Nenhum checkpoint pendente."));
    return;
  }

  for (const checkpoint of checkpoints) {
    const item = document.createElement("div");
    item.className = "checkpoint";
    const title = document.createElement("strong");
    title.textContent = `${checkpoint.checkpoint_id}. ${checkpoint.label || "Checkpoint"}`;
    const risk = document.createElement("span");
    risk.className = `risk ${riskClass(checkpoint.reason)}`;
    risk.textContent = riskLabel(checkpoint.reason);
    const detail = document.createElement("p");
    detail.textContent = checkpoint.checkpoint_detail || `${checkpoint.plan || "plano"} - ${checkpoint.reason || "revisao"}`;
    const meta = document.createElement("p");
    meta.className = "checkpoint-meta";
    meta.textContent = checkpointMeta(checkpoint);
    const next = document.createElement("p");
    next.textContent = checkpoint.next_step || "Revise antes de confirmar.";
    next.className = "next-step";
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `Confirmar ${checkpoint.checkpoint_id}`;
    button.addEventListener("click", () => sendCommand(`confirmar checkpoint ${checkpoint.checkpoint_id}`, true));
    item.append(title, risk, detail, meta, next, button);
    nodes.checkpointList.append(item);
  }
}

function checkpointMeta(checkpoint) {
  const parts = [checkpoint.source_label || checkpoint.plan || "plano"];
  if (checkpoint.step_index) {
    parts.push(`etapa ${checkpoint.step_index}`);
  }
  if (checkpoint.command) {
    parts.push(`comando: ${checkpoint.command}`);
  } else if (checkpoint.step_label) {
    parts.push(checkpoint.step_label);
  }
  return parts.join(" | ");
}

function renderCheckpointEvents(events) {
  nodes.checkpointEvents.replaceChildren();
  if (!events.length) {
    nodes.checkpointEvents.append(emptyText("Nenhum evento recente."));
    return;
  }

  for (const event of events.slice(0, 5)) {
    const item = document.createElement("div");
    item.className = "event";
    const title = document.createElement("strong");
    title.textContent = `${event.label || "Checkpoint"} -> ${event.status || "unknown"}`;
    const detail = document.createElement("p");
    detail.textContent = event.event_detail || event.message || `${event.reason || "sem motivo"} - ${event.created_at || "agora"}`;
    const meta = document.createElement("p");
    meta.className = "checkpoint-meta";
    meta.textContent = eventMeta(event);
    const next = document.createElement("p");
    next.className = "next-step";
    next.textContent = event.next_step || "Nenhuma acao pendente.";
    item.append(title, detail, meta, next);
    nodes.checkpointEvents.append(item);
  }
}

function eventMeta(event) {
  const parts = [event.source_label || event.plan || "evento"];
  if (event.step_index) {
    parts.push(`etapa ${event.step_index}`);
  }
  if (event.command) {
    parts.push(`comando: ${event.command}`);
  } else if (event.step_label) {
    parts.push(event.step_label);
  }
  return parts.join(" | ");
}

function renderHistory(commands) {
  nodes.historyList.replaceChildren();
  if (!commands.length) {
    const item = document.createElement("li");
    item.textContent = "Nenhum comando registrado.";
    nodes.historyList.append(item);
    return;
  }

  for (const command of commands) {
    const item = document.createElement("li");
    const action = command.action || {};
    item.textContent = `${command.text || ""} -> ${action.skill || "core"}.${action.name || "acao"}`;
    nodes.historyList.append(item);
  }
}

function renderMemoryAudit(audit) {
  const byIntent = audit.by_intent || [];
  const bySkill = audit.by_skill || [];
  renderDefinitionList(nodes.memoryAuditList, [
    ["Total", String(audit.matching_count || 0)],
    ["Primeiro", audit.first_command_at || "nenhum"],
    ["Ultimo", audit.latest_command_at || "nenhum"],
    ["Intencoes", formatCounts(byIntent)],
    ["Skills", formatCounts(bySkill)],
  ]);

  nodes.memoryAuditSample.replaceChildren();
  const sample = audit.sample || [];
  if (!sample.length) {
    const item = document.createElement("li");
    item.textContent = "Nenhuma memoria auditavel.";
    nodes.memoryAuditSample.append(item);
    return;
  }

  for (const command of sample.slice(0, 5)) {
    const item = document.createElement("li");
    item.className = "memory-row";
    const action = command.action || {};
    const detail = document.createElement("span");
    detail.textContent = `#${command.id || "?"} ${command.text || ""} -> ${action.skill || "core"}.${action.name || "acao"} (${action.status || "unknown"})`;
    item.append(detail);
    if (command.id) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "danger-button";
      button.textContent = "Apagar";
      button.addEventListener("click", () => deleteMemoryById(command.id));
      item.append(button);
    }
    nodes.memoryAuditSample.append(item);
  }
}

async function loadMemoryAudit(filters, announce = true) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      params.set(key, value);
    }
  }
  const query = params.toString();
  const audit = await requestJson(query ? `/history/audit?${query}` : "/history/audit");
  renderMemoryAudit(audit);
  if (announce) {
    nodes.lastResponse.textContent = `Auditoria filtrada: ${audit.matching_count || 0} comando(s).`;
  }
}

function renderNextActions(actions) {
  nodes.nextActions.replaceChildren();
  if (!actions.length) {
    nodes.nextActions.append(emptyText("Nenhuma sugestao no momento."));
    return;
  }

  for (const action of actions) {
    const item = normalizeAction(action);
    const button = document.createElement("button");
    button.type = "button";
    button.className = `action-button risk-${item.risk}`;
    button.disabled = !item.enabled;
    button.textContent = item.requires_confirmation ? `${item.label} - confirmar` : item.label;
    button.title = actionTitle(item);
    button.addEventListener("click", () => {
      sendCommand(item.command, item.requires_confirmation);
    });
    nodes.nextActions.append(button);
  }
}

function normalizeAction(action) {
  if (typeof action === "string") {
    return {
      label: action,
      command: action,
      risk: "low",
      enabled: true,
      requires_confirmation: action.startsWith("confirmar checkpoint"),
      reason: "legacy",
    };
  }
  return {
    label: action.label || action.command || "acao",
    command: action.command || action.label || "",
    risk: action.risk || "low",
    enabled: action.enabled !== false,
    requires_confirmation: Boolean(action.requires_confirmation),
    permission: action.permission || null,
    reason: action.reason || "suggested",
    risk_reason: action.risk_reason || null,
    risk_category: action.risk_category || null,
  };
}

function actionTitle(action) {
  const parts = [`risco: ${action.risk}`, `motivo: ${action.reason}`];
  if (action.risk_reason && action.risk_reason !== action.reason) {
    parts.push(`politica: ${action.risk_reason}`);
  }
  if (action.risk_category) {
    parts.push(`categoria: ${action.risk_category}`);
  }
  if (action.permission) {
    parts.push(`permissao: ${action.permission}`);
  }
  return parts.join(" | ");
}

function emptyText(text) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  return paragraph;
}

function formatCounts(items) {
  if (!items.length) return "nenhum";
  return items.slice(0, 3).map((item) => `${item.name || "unknown"}=${item.count || 0}`).join(", ");
}

function collectMemoryAuditFilters() {
  return {
    intent: nodes.memoryAuditIntent.value.trim(),
    skill: nodes.memoryAuditSkill.value.trim(),
    action: nodes.memoryAuditAction.value.trim(),
    since: nodes.memoryAuditSince.value,
    until: nodes.memoryAuditUntil.value,
    limit: nodes.memoryAuditLimit.value || "5",
  };
}

function hasActiveMemoryAuditFilter(filters) {
  return Boolean(filters.intent || filters.skill || filters.action || filters.since || filters.until);
}

async function deleteMemoryById(commandId) {
  if (!window.confirm(`Apagar o comando ${commandId} da memoria local?`)) return;
  await deleteMemory({command_ids: [commandId], confirm: true});
}

async function deleteFilteredMemory() {
  const filters = collectMemoryAuditFilters();
  if (!hasActiveMemoryAuditFilter(filters)) {
    nodes.lastResponse.textContent = "Aplique um filtro antes de apagar memorias em lote.";
    return;
  }
  if (!window.confirm("Apagar as memorias que correspondem ao filtro atual?")) return;
  await deleteMemory({...filters, confirm: true});
}

async function deleteMemory(payload) {
  setBusy(true);
  try {
    const result = await requestJson("/history/delete", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    nodes.lastResponse.textContent = `Memoria atualizada: ${result.deleted || 0} comando(s) apagado(s).`;
    await loadState();
  } catch (error) {
    nodes.lastResponse.textContent = `Falha ao apagar memoria: ${error.message}`;
    nodes.lastResponse.classList.add("error");
  } finally {
    setBusy(false);
  }
}

async function sendCommand(text, confirmActions = false) {
  const command = text.trim();
  if (!command) return;

  setBusy(true);
  try {
    const payload = await requestJson("/command", {
      method: "POST",
      body: JSON.stringify({
        text: command,
        confirm_actions: confirmActions || nodes.confirm.checked,
        private: nodes.private.checked,
      }),
    });
    nodes.lastResponse.textContent = payload.response || "Comando processado.";
    nodes.input.value = "";
    await loadState();
  } catch (error) {
    nodes.lastResponse.textContent = `Falha ao executar: ${error.message}`;
    nodes.lastResponse.classList.add("error");
  } finally {
    setBusy(false);
  }
}

async function postSessionAction(path) {
  setBusy(true);
  try {
    const payload = await requestJson(path, {method: "POST", body: "{}"});
    nodes.lastResponse.textContent = `Sessao: ${payload.status || "ok"}`;
    await loadState();
  } catch (error) {
    nodes.lastResponse.textContent = `Falha na sessao: ${error.message}`;
    nodes.lastResponse.classList.add("error");
  } finally {
    setBusy(false);
  }
}

function setBusy(isBusy) {
  for (const button of document.querySelectorAll("button")) {
    button.disabled = isBusy;
  }
}

function riskLabel(reason) {
  if (reason === "shell_disabled") return "shell bloqueado";
  if (reason === "confirmation_required") return "confirmacao";
  if (reason === "permission_required") return "permissao";
  return reason || "revisao";
}

function riskClass(reason) {
  if (reason === "shell_disabled") return "blocked";
  if (reason === "confirmation_required") return "review";
  return "neutral";
}

function configureRefresh() {
  const saved = window.localStorage.getItem("jarvis.refreshInterval");
  if (saved) {
    nodes.refreshInterval.value = saved;
  }
  scheduleRefresh();
}

function scheduleRefresh() {
  if (state.refreshTimer) {
    window.clearInterval(state.refreshTimer);
    state.refreshTimer = null;
  }
  const interval = Number(nodes.refreshInterval.value || 0);
  window.localStorage.setItem("jarvis.refreshInterval", String(interval));
  if (interval > 0) {
    state.refreshTimer = window.setInterval(loadState, interval);
  }
}

nodes.form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendCommand(nodes.input.value);
});

nodes.memoryAuditForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const filters = collectMemoryAuditFilters();
  state.memoryAuditFilters = hasActiveMemoryAuditFilter(filters) ? filters : null;
  setBusy(true);
  try {
    await loadMemoryAudit(filters);
  } catch (error) {
    nodes.lastResponse.textContent = `Falha ao filtrar memoria: ${error.message}`;
    nodes.lastResponse.classList.add("error");
  } finally {
    setBusy(false);
  }
});

nodes.memoryAuditClear.addEventListener("click", async () => {
  nodes.memoryAuditForm.reset();
  nodes.memoryAuditLimit.value = "5";
  state.memoryAuditFilters = null;
  await loadState();
});

nodes.memoryAuditDeleteFiltered.addEventListener("click", deleteFilteredMemory);

nodes.pauseButton.addEventListener("click", () => postSessionAction("/pause"));
nodes.resumeButton.addEventListener("click", () => postSessionAction("/resume"));
nodes.refreshButton.addEventListener("click", loadState);
nodes.refreshInterval.addEventListener("change", scheduleRefresh);

loadState();
configureRefresh();
