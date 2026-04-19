from pathlib import Path
from typing import Any

from .checkpoints import build_checkpoint_state
from .presence import build_presence
from .proactive import build_proactive_suggestions
from .risk import apply_profile, classify_capability, classify_command_text, classify_checkpoint
from .skills.ide import detect_project_commands, detect_project_state


def build_ui_state(
    context: dict[str, Any],
    session: dict[str, Any],
    memory_store: Any,
    history_limit: int = 5,
) -> dict[str, Any]:
    presence = build_presence(context, session=session, mode="text")
    checkpoints = build_checkpoint_state(session)
    privacy = _build_privacy_state(context, session, memory_store)
    history = {
        "limit": history_limit,
        "commands": memory_store.recent_commands(limit=history_limit) if memory_store else [],
    }
    memory_audit = _build_memory_audit(memory_store, limit=history_limit)
    capabilities = _build_capabilities(context)
    proactive = {
        "suggestions": build_proactive_suggestions(
            context,
            history=history["commands"],
            project_state=capabilities["state"],
        )
    }

    return {
        "schema_version": 1,
        "presence": presence,
        "checkpoints": checkpoints,
        "history": history,
        "memory_audit": memory_audit,
        "privacy": privacy,
        "capabilities": capabilities,
        "proactive": proactive,
        "actions": _build_actions(presence, checkpoints, proactive["suggestions"]),
        "next_actions": _build_next_actions(presence, checkpoints, proactive["suggestions"]),
    }


def _build_privacy_state(context: dict[str, Any], session: dict[str, Any], memory_store: Any) -> dict[str, Any]:
    privacy = context["privacy"]
    return {
        "privacy": privacy,
        "permissions": {
            "cloud_enabled": privacy["cloud_enabled"],
            "browser_actions_enabled": privacy.get("browser_actions_enabled", False),
            "desktop_actions_enabled": privacy["desktop_actions_enabled"],
            "ide_actions_enabled": privacy.get("ide_actions_enabled", False),
            "shell_enabled": privacy["shell_enabled"],
            "media_actions_enabled": privacy.get("media_actions_enabled", False),
        },
        "memory": memory_store.stats() if memory_store else {"enabled": False},
        "session": session,
    }


def _build_memory_audit(memory_store: Any, limit: int) -> dict[str, Any]:
    if memory_store is None:
        return {
            "generated_at": None,
            "filters": {"limit": limit},
            "stats": {"enabled": False},
            "matching_count": 0,
            "first_command_at": None,
            "latest_command_at": None,
            "by_intent": [],
            "by_skill": [],
            "by_action": [],
            "by_status": [],
            "sample": [],
        }
    return memory_store.audit_summary(limit=limit)


def _build_next_actions(
    presence: dict[str, Any],
    checkpoints: dict[str, Any],
    proactive: list[dict[str, Any]],
) -> list[str]:
    actions = []
    if checkpoints["pending_count"]:
        actions.extend(
            f"confirmar checkpoint {checkpoint['checkpoint_id']}"
            for checkpoint in checkpoints["checkpoints"][:3]
        )
    actions.extend(action["command"] for action in proactive)
    actions.extend(presence.get("suggestions", []))
    return list(dict.fromkeys(actions))[:6]


def _build_actions(
    presence: dict[str, Any],
    checkpoints: dict[str, Any],
    proactive: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions = []
    for checkpoint in checkpoints["checkpoints"][:3]:
        checkpoint_id = checkpoint["checkpoint_id"]
        reason = checkpoint.get("reason", "confirmation_required")
        action = {
            "id": f"checkpoint-{checkpoint_id}",
            "label": f"Confirmar checkpoint {checkpoint_id}",
            "command": f"confirmar checkpoint {checkpoint_id}",
            "kind": "checkpoint",
            "enabled": True,
            "reason": reason,
        }
        actions.append(
            apply_profile(action, classify_checkpoint(checkpoint))
        )

    actions.extend(proactive)

    for index, suggestion in enumerate(presence.get("suggestions", []), start=1):
        action = {
            "id": f"suggestion-{index}",
            "label": suggestion,
            "command": suggestion,
            "kind": "suggestion",
            "enabled": True,
            "reason": "suggested",
        }
        actions.append(
            apply_profile(action, classify_command_text(suggestion))
        )

    return _dedupe_actions(actions)[:6]


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


def _build_capabilities(context: dict[str, Any]) -> dict[str, Any]:
    privacy = context["privacy"]
    commands = detect_project_commands(Path(context["project"]["path"]))
    actions = [
        _capability("shell.run_command", "Executar comandos de shell", privacy["shell_enabled"], "JARVIS_ENABLE_SHELL"),
        _capability("ide.open_project", "Abrir projeto na IDE", privacy.get("ide_actions_enabled", False), "JARVIS_ENABLE_IDE_ACTIONS"),
        _capability("browser.open_url", "Abrir navegador", privacy.get("browser_actions_enabled", False), "JARVIS_ENABLE_BROWSER_ACTIONS"),
        _capability("media.control", "Controlar midia e volume", privacy.get("media_actions_enabled", False), "JARVIS_ENABLE_MEDIA_ACTIONS"),
        _capability("desktop.open_app", "Abrir aplicativos", privacy["desktop_actions_enabled"], "JARVIS_ENABLE_DESKTOP_ACTIONS"),
    ]
    return {
        "project": context["project"]["capabilities"],
        "state": detect_project_state(Path(context["project"]["path"])),
        "commands": {
            "count": len(commands),
            "items": commands[:10],
        },
        "actions": actions,
        "enabled_count": len([action for action in actions if action["enabled"]]),
        "blocked_count": len([action for action in actions if not action["enabled"]]),
    }


def _capability(capability_id: str, label: str, enabled: bool, env_var: str) -> dict[str, Any]:
    profile = classify_capability(capability_id, enabled=enabled)
    return {
        "id": capability_id,
        "label": label,
        "enabled": enabled,
        "status": "enabled" if enabled else "blocked",
        "env_var": env_var,
        **profile.to_dict(),
    }
