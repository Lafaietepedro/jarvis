const state = {
  loading: false,
};

const nodes = {
  title: document.querySelector("#status-title"),
  greeting: document.querySelector("#greeting"),
  statePill: document.querySelector("#state-pill"),
  presenceList: document.querySelector("#presence-list"),
  privacyList: document.querySelector("#privacy-list"),
  checkpointList: document.querySelector("#checkpoint-list"),
  historyList: document.querySelector("#history-list"),
  nextActions: document.querySelector("#next-actions"),
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
  ]);

  renderDefinitionList(nodes.privacyList, [
    ["Nuvem", permissions.cloud_enabled ? "ativa" : "desligada"],
    ["Memoria", memory.enabled ? "ativa" : "desligada"],
    ["Comandos", String(memory.commands_recorded || 0)],
    ["Shell", permissions.shell_enabled ? "permitido" : "bloqueado"],
    ["IDE", permissions.ide_actions_enabled ? "permitida" : "bloqueada"],
    ["Midia", permissions.media_actions_enabled ? "permitida" : "bloqueada"],
  ]);

  renderCheckpoints(checkpoints.checkpoints || []);
  renderHistory((payload.history || {}).commands || []);
  renderNextActions(payload.next_actions || []);
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
    const detail = document.createElement("p");
    detail.textContent = `${checkpoint.plan || "plano"} - ${checkpoint.reason || "revisao"}`;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `Confirmar ${checkpoint.checkpoint_id}`;
    button.addEventListener("click", () => sendCommand(`confirmar checkpoint ${checkpoint.checkpoint_id}`, true));
    item.append(title, detail, button);
    nodes.checkpointList.append(item);
  }
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

function renderNextActions(actions) {
  nodes.nextActions.replaceChildren();
  if (!actions.length) {
    nodes.nextActions.append(emptyText("Nenhuma sugestao no momento."));
    return;
  }

  for (const action of actions) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = action;
    button.addEventListener("click", () => {
      const needsConfirmation = action.startsWith("confirmar checkpoint");
      sendCommand(action, needsConfirmation);
    });
    nodes.nextActions.append(button);
  }
}

function emptyText(text) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  return paragraph;
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

nodes.form.addEventListener("submit", (event) => {
  event.preventDefault();
  sendCommand(nodes.input.value);
});

nodes.pauseButton.addEventListener("click", () => postSessionAction("/pause"));
nodes.resumeButton.addEventListener("click", () => postSessionAction("/resume"));
nodes.refreshButton.addEventListener("click", loadState);

loadState();
window.setInterval(loadState, 5000);
