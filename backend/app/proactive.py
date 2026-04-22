from typing import Any

from .risk import apply_profile, classify_command_text


def build_proactive_suggestions(
    context: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    project_state: dict[str, Any] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    history = history or []
    project = context.get("project", {})
    capabilities = project.get("capabilities", {})
    state = project_state or {}
    markers = set(state.get("markers") or project.get("markers") or [])
    commands = state.get("commands", {}).get("items", [])

    suggestions: list[dict[str, Any]] = []

    latest_intent = _latest_intent(history)
    if not history:
        _add(suggestions, "estado do projeto", "no_recent_history")
    elif latest_intent in {"status", "system_status"}:
        _add(suggestions, "estado do projeto", "after_status")
        _add(suggestions, "checkup do projeto", "after_status")
    elif latest_intent == "project_commands":
        test_command = _preferred_test_command(commands)
        command = f"rodar {test_command}" if test_command else "checkup do projeto"
        _add(suggestions, command, "after_project_commands")
    elif latest_intent == "project_state":
        _add(suggestions, "checkup do projeto", "after_project_snapshot")
    elif latest_intent == "confirm_checkpoint" and _latest_edit_audit(history):
        _add(suggestions, "desfazer ultima edicao", "after_file_edit")
    elif latest_intent == "command_history":
        _add(suggestions, "exportar historico", "after_history_review")

    if _intent_count(history, "status") >= 2:
        _add(suggestions, "checkup do projeto", "repeated_status_checks")

    test_command = _preferred_test_command(commands)
    if test_command:
        _add(suggestions, f"rodar {test_command}", "project_test_command")

    if commands:
        _add(suggestions, "comandos do projeto", "project_commands_available")

    if "README.md" in markers:
        _add(suggestions, "analisar projeto", "project_readme")

    if capabilities.get("has_docker_compose") or "docker-compose.yml" in markers:
        _add(suggestions, "subir ambiente com docker compose", "docker_compose_available")

    _add(suggestions, "ver ultimos comandos", "local_memory_audit")
    return _dedupe_actions(suggestions)[:limit]


def _add(suggestions: list[dict[str, Any]], command: str, reason: str):
    action = {
        "id": f"proactive-{len(suggestions) + 1}",
        "label": command,
        "command": command,
        "kind": "proactive",
        "enabled": True,
        "reason": reason,
    }
    suggestions.append(apply_profile(action, classify_command_text(command)))


def _preferred_test_command(commands: list[dict[str, Any]]) -> str | None:
    values = [command.get("command", "") for command in commands]
    for preferred in ("make test", "npm run test"):
        if preferred in values:
            return preferred

    for value in values:
        if "test" in value:
            return value
    return None


def _latest_intent(history: list[dict[str, Any]]) -> str | None:
    if not history:
        return None
    return history[0].get("intent", {}).get("intent")


def _intent_count(history: list[dict[str, Any]], name: str) -> int:
    return sum(1 for command in history if command.get("intent", {}).get("intent") == name)


def _latest_edit_audit(history: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not history:
        return None
    action = history[0].get("action", {})
    edit_audit = action.get("edit_audit")
    if isinstance(edit_audit, dict):
        return edit_audit
    delegated = action.get("delegated_action")
    if isinstance(delegated, dict):
        delegated_audit = delegated.get("edit_audit")
        if isinstance(delegated_audit, dict):
            return delegated_audit
    return None


def _dedupe_actions(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for action in actions:
        command = action["command"]
        if command in seen:
            continue
        seen.add(command)
        unique.append(action)
    return unique
