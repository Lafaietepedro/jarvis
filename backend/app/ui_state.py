from typing import Any

from .checkpoints import build_checkpoint_state
from .presence import build_presence


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

    return {
        "schema_version": 1,
        "presence": presence,
        "checkpoints": checkpoints,
        "history": history,
        "privacy": privacy,
        "next_actions": _build_next_actions(presence, checkpoints),
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


def _build_next_actions(presence: dict[str, Any], checkpoints: dict[str, Any]) -> list[str]:
    actions = []
    if checkpoints["pending_count"]:
        actions.extend(
            f"confirmar checkpoint {checkpoint['checkpoint_id']}"
            for checkpoint in checkpoints["checkpoints"][:3]
        )
    actions.extend(presence.get("suggestions", []))
    return list(dict.fromkeys(actions))[:6]
