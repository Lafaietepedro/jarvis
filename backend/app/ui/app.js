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
    const preview = renderEditPreview(checkpoint.edit_preview);
    const diff = renderDiff(checkpoint.diff);
    item.append(title, risk, detail, meta);
    if (preview) {
      item.append(preview);
    }
    if (diff) {
      item.append(diff);
    }
    item.append(next);
    const actions = renderCheckpointActions(checkpoint);
    if (actions) {
      item.append(actions);
    }
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
  if (checkpoint.path) {
    parts.push(`arquivo: ${checkpoint.path}`);
  }
  if (checkpoint.occurrences > 1) {
    parts.push(`ocorrencias: ${checkpoint.occurrences}`);
  }
  if (checkpoint.source_command_id) {
    parts.push(`origem: #${checkpoint.source_command_id}`);
  }
  return parts.join(" | ");
}

function renderDiff(value) {
  if (!value) {
    return null;
  }
  const diff = document.createElement("pre");
  diff.className = "checkpoint-diff";
  diff.textContent = value;
  return diff;
}

function renderEditPreview(preview) {
  if (!preview || (!preview.before && !preview.after)) {
    return null;
  }
  const wrapper = document.createElement("div");
  wrapper.className = "edit-preview";
  const title = document.createElement("p");
  title.className = "checkpoint-meta";
  title.textContent = preview.has_multiple_matches
    ? `Contexto da primeira ocorrencia entre ${preview.occurrence_count} encontradas`
    : "Contexto da edicao";
  wrapper.append(title);
  if (preview.before) {
    wrapper.append(renderEditPreviewBlock("Antes", preview.before));
  }
  if (preview.after) {
    wrapper.append(renderEditPreviewBlock("Depois", preview.after));
  }
  return wrapper;
}

function renderEditPreviewBlock(label, block) {
  const section = document.createElement("div");
  section.className = "edit-preview-block";
  const heading = document.createElement("strong");
  heading.textContent = `${label} (${lineSpanLabel(block)})`;
  const text = document.createElement("pre");
  text.className = "checkpoint-diff";
  text.textContent = block.text || "";
  section.append(heading, text);
  return section;
}

function lineSpanLabel(block) {
  const start = block.line_start;
  const end = block.line_end;
  if (!start || !end) {
    return "sem linhas";
  }
  const window = start === end ? `linha ${start}` : `linhas ${start}-${end}`;
  if (!block.focus_start || !block.focus_end) {
    return window;
  }
  const focus = block.focus_start === block.focus_end
    ? `alvo ${block.focus_start}`
    : `alvo ${block.focus_start}-${block.focus_end}`;
  return `${window}, ${focus}`;
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
    const actions = renderCheckpointEventActions(event);
    if (actions) {
      item.append(actions);
    }
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
  if (event.source_command_id) {
    parts.push(`origem: #${event.source_command_id}`);
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
    item.className = "history-row";
    if (command.id) {
      item.dataset.historyCommandId = String(command.id);
    }
    const details = document.createElement("div");
    details.className = "history-details";
    const action = command.action || {};
    const title = document.createElement("div");
    title.textContent = `${command.text || ""} -> ${action.skill || "core"}.${action.name || "acao"}`;
    details.append(title);
    const editAudit = resolveEditAudit(command);
    if (editAudit) {
      details.append(historyMeta(`Edit: ${editAudit.summary || editAudit.path || "arquivo local"}`));
      if (editAudit.revert_command) {
        details.append(historyMeta(`Reverter: ${editAudit.revert_command}`));
      }
    }
    item.append(details);
    const actions = renderHistoryActions(command, {allowDelete: false});
    if (actions) {
      item.append(actions);
    }
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
    if (command.id) {
      item.dataset.historyCommandId = String(command.id);
    }
    const details = document.createElement("div");
    details.className = "history-details";
    const action = command.action || {};
    const detail = document.createElement("span");
    detail.textContent = `#${command.id || "?"} ${command.text || ""} -> ${action.skill || "core"}.${action.name || "acao"} (${action.status || "unknown"})`;
    details.append(detail);
    const editAudit = resolveEditAudit(command);
    if (editAudit) {
      details.append(historyMeta(`Edit: ${editAudit.summary || editAudit.path || "arquivo local"}`));
    }
    item.append(details);
    const actions = renderHistoryActions(command, {allowDelete: true});
    if (actions) {
      item.append(actions);
    }
    nodes.memoryAuditSample.append(item);
  }
}

function renderHistoryActions(command, options = {}) {
  const actions = document.createElement("div");
  actions.className = "history-actions";
  const editAudit = resolveEditAudit(command);
  if (editAudit && editAudit.revert_command) {
    const revert = document.createElement("button");
    revert.type = "button";
    revert.className = "secondary-button";
    revert.textContent = "Preparar reversao";
    revert.addEventListener("click", () => prepareRevert(editAudit.revert_command));
    actions.append(revert);
  }
  if (options.allowDelete && command.id) {
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "danger-button";
    remove.textContent = "Apagar";
    remove.addEventListener("click", () => deleteMemoryById(command.id));
    actions.append(remove);
  }
  return actions.childElementCount ? actions : null;
}

function historyMeta(text) {
  const meta = document.createElement("span");
  meta.className = "history-meta";
  meta.textContent = text;
  return meta;
}

function resolveEditAudit(command) {
  const action = command.action || {};
  if (action.edit_audit) {
    return action.edit_audit;
  }
  if (action.delegated_action && action.delegated_action.edit_audit) {
    return action.delegated_action.edit_audit;
  }
  return null;
}

async function loadMemoryAudit(filters, announce = true) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== null && value !== undefined && value !== "") {
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

async function prepareRevert(command) {
  await sendCommand(command, false);
}

function renderCheckpointActions(checkpoint) {
  const actions = document.createElement("div");
  actions.className = "checkpoint-actions";
  if (checkpoint.source_command_id) {
    const origin = document.createElement("button");
    origin.type = "button";
    origin.className = "secondary-button";
    origin.textContent = `Ver origem #${checkpoint.source_command_id}`;
    origin.addEventListener("click", () => jumpToHistoryCommand(checkpoint.source_command_id));
    actions.append(origin);
  }
  const confirm = document.createElement("button");
  confirm.type = "button";
  confirm.textContent = `Confirmar ${checkpoint.checkpoint_id}`;
  confirm.addEventListener("click", () => sendCommand(`confirmar checkpoint ${checkpoint.checkpoint_id}`, true));
  actions.append(confirm);
  return actions;
}

function renderCheckpointEventActions(event) {
  const actions = document.createElement("div");
  actions.className = "checkpoint-actions";
  if (event.source_command_id) {
    const origin = document.createElement("button");
    origin.type = "button";
    origin.className = "secondary-button";
    origin.textContent = `Ver origem #${event.source_command_id}`;
    origin.addEventListener("click", () => jumpToHistoryCommand(event.source_command_id));
    actions.append(origin);
  }
  const editAudit = resolveEventEditAudit(event);
  if (editAudit && editAudit.revert_command) {
    const revert = document.createElement("button");
    revert.type = "button";
    revert.className = "secondary-button";
    revert.textContent = "Preparar reversao";
    revert.addEventListener("click", () => prepareRevert(editAudit.revert_command));
    actions.append(revert);
  }
  return actions.childElementCount ? actions : null;
}

function resolveEventEditAudit(event) {
  if (event.edit_audit) {
    return event.edit_audit;
  }
  return null;
}

async function jumpToHistoryCommand(commandId) {
  let target = findHistoryCommandNode(commandId);
  if (!target) {
    target = await locateHistoryCommand(commandId);
  }
  if (!target) {
    nodes.lastResponse.textContent = `Nao encontrei a origem #${commandId} na memoria local.`;
    return;
  }
  highlightHistoryTarget(target);
}

function findHistoryCommandNode(commandId) {
  return document.querySelector(`[data-history-command-id="${commandId}"]`);
}

async function locateHistoryCommand(commandId) {
  const audit = await requestJson(`/history/audit?command_id=${encodeURIComponent(commandId)}&limit=1`);
  renderMemoryAudit(audit);
  if (!(audit.sample || []).length) {
    return null;
  }
  nodes.lastResponse.textContent = `Origem #${commandId} localizada na memoria auditavel.`;
  return findHistoryCommandNode(commandId);
}

function highlightHistoryTarget(target) {
  target.scrollIntoView({behavior: "smooth", block: "center"});
  target.classList.add("highlighted");
  window.setTimeout(() => target.classList.remove("highlighted"), 1800);
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
