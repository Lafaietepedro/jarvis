from typing import Any


def format_presence(payload: dict[str, Any]) -> str:
    project = payload.get("project", {})
    privacy = payload.get("privacy", {})
    lines = [
        "[JARVIS]",
        f"Status: {payload.get('status', 'unknown')}",
        f"Voice: {'listening' if payload.get('voice_listening') else 'idle'}",
        f"Project: {project.get('name', 'unknown')} ({project.get('path', 'unknown')})",
        f"Uptime: {payload.get('uptime_seconds', 0)}s",
        f"Cloud: {'enabled' if privacy.get('cloud_enabled') else 'disabled'}",
        f"Memory: {'enabled' if privacy.get('memory_enabled') else 'disabled'}",
        "",
        payload.get("greeting", ""),
    ]
    return "\n".join(line for line in lines if line is not None)


def format_privacy(payload: dict[str, Any]) -> str:
    data = payload.get("data", {})
    permissions = data.get("permissions", {})
    memory = data.get("memory", {})
    session = data.get("session", {})
    lines = [
        "[PRIVACY]",
        f"Cloud enabled: {permissions.get('cloud_enabled', False)}",
        f"Browser actions: {permissions.get('browser_actions_enabled', False)}",
        f"Desktop actions: {permissions.get('desktop_actions_enabled', False)}",
        f"IDE actions: {permissions.get('ide_actions_enabled', False)}",
        f"Shell actions: {permissions.get('shell_enabled', False)}",
        f"Media actions: {permissions.get('media_actions_enabled', False)}",
        f"Memory enabled: {memory.get('enabled', False)}",
        f"Commands recorded: {memory.get('commands_recorded', 0)}",
        f"Memory path: {memory.get('path', 'unavailable')}",
        f"Session: {session.get('status', 'unknown')}",
    ]
    return "\n".join(lines)


def format_history(payload: dict[str, Any]) -> str:
    commands = payload.get("commands", [])
    lines = ["[HISTORY]"]
    if not commands:
        lines.append("No commands recorded yet.")
        return "\n".join(lines)

    for index, command in enumerate(commands, start=1):
        action = command.get("action", {})
        lines.append(
            f"{index}. {command.get('text', '')} -> "
            f"{action.get('skill', 'unknown')}.{action.get('name', 'unknown')} "
            f"({action.get('status', 'unknown')})"
        )
    return "\n".join(lines)


def format_history_export(payload: dict[str, Any]) -> str:
    stats = payload.get("stats", {})
    commands = payload.get("commands", [])
    lines = [
        "[HISTORY EXPORT]",
        f"Exported at: {payload.get('exported_at', 'unknown')}",
        f"Commands exported: {len(commands)}",
        f"Memory path: {stats.get('path', 'unavailable')}",
    ]
    return "\n".join(lines)


def format_command_result(payload: dict[str, Any]) -> str:
    action = payload.get("action", {})
    suggestions = payload.get("suggestions", [])
    lines = [
        "[COMMAND]",
        f"Response: {payload.get('response', '')}",
        f"Intent: {payload.get('intent', {}).get('intent', 'unknown')}",
        f"Action: {action.get('skill', 'unknown')}.{action.get('name', 'unknown')} ({action.get('status', 'unknown')})",
    ]
    if action.get("reason"):
        lines.append(f"Reason: {action['reason']}")
    if suggestions:
        lines.append("")
        lines.append("Suggestions:")
        lines.extend(f"- {suggestion}" for suggestion in suggestions)
    return "\n".join(lines)


def format_diagnostics(payload: dict[str, Any]) -> str:
    platform = payload.get("platform", {})
    audio = payload.get("audio", {})
    binaries = payload.get("binaries", {})
    missing = [name for name, item in binaries.items() if not item.get("available")]
    available_count = len(binaries) - len(missing)
    lines = [
        "[DIAGNOSTICS]",
        f"System: {platform.get('system', 'unknown')} {platform.get('release', '')}".strip(),
        f"Python: {platform.get('python', 'unknown')}",
        f"Vosk model: {'available' if audio.get('vosk_model_available') else 'missing'}",
        f"Optional binaries: {available_count}/{len(binaries)} available",
    ]
    if missing:
        lines.append(f"Missing: {', '.join(missing)}")
    return "\n".join(lines)


def format_panel(
    presence: dict[str, Any],
    privacy: dict[str, Any],
    history: dict[str, Any],
    diagnostics: dict[str, Any] | None = None,
) -> str:
    sections = [
        format_presence(presence),
        format_privacy(privacy),
        format_history(history),
    ]
    if diagnostics is not None:
        sections.append(format_diagnostics(diagnostics))
    return "\n\n".join(sections)
