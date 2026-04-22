from typing import Any


def format_presence(payload: dict[str, Any]) -> str:
    project = payload.get("project", {})
    privacy = payload.get("privacy", {})
    checkpoints = _extract_checkpoints(payload)
    checkpoint_events = _extract_checkpoint_events(payload)
    lines = [
        "[JARVIS]",
        f"Status: {payload.get('status', 'unknown')}",
        f"Voice: {'listening' if payload.get('voice_listening') else 'idle'}",
        f"Project: {project.get('name', 'unknown')} ({project.get('path', 'unknown')})",
        f"Uptime: {payload.get('uptime_seconds', 0)}s",
        f"Pending checkpoints: {len(checkpoints)}",
        f"Checkpoint events: {len(checkpoint_events)}",
        f"Cloud: {'enabled' if privacy.get('cloud_enabled') else 'disabled'}",
        f"Memory: {'enabled' if privacy.get('memory_enabled') else 'disabled'}",
        "",
        payload.get("greeting", ""),
    ]
    return "\n".join(line for line in lines if line is not None)


def format_checkpoints(payload: dict[str, Any]) -> str:
    checkpoints = _extract_checkpoints(payload)
    checkpoint_events = _extract_checkpoint_events(payload)
    summary = payload.get("summary", {})
    lines = ["[CHECKPOINTS]"]
    if summary:
        lines.append(
            f"Summary: pending={summary.get('pending', 0)} blocked_events={summary.get('blocked_events', 0)}"
        )
        if summary.get("next_step"):
            lines.append(f"Next: {summary['next_step']}")
    if checkpoints:
        for checkpoint in checkpoints:
            checkpoint_id = checkpoint.get("checkpoint_id", "?")
            plan = checkpoint.get("plan", "unknown")
            label = checkpoint.get("label", "unknown")
            reason = checkpoint.get("reason", "unknown")
            lines.append(f"{checkpoint_id}. {label} [{plan}]")
            if checkpoint.get("checkpoint_detail"):
                lines.append(f"   Detail: {checkpoint['checkpoint_detail']}")
            context = _format_checkpoint_context(checkpoint)
            if context:
                lines.append(f"   Context: {context}")
            lines.append(f"   Reason: {reason}")
            if checkpoint.get("risk"):
                risk_line = f"   Risk: {checkpoint['risk']}"
                if checkpoint.get("permission"):
                    risk_line += f" ({checkpoint['permission']})"
                lines.append(risk_line)
            if checkpoint.get("command"):
                lines.append(f"   Command: {checkpoint['command']}")
            if checkpoint.get("replacement_strategy") == "first_occurrence" and checkpoint.get("occurrences", 0) > 1:
                lines.append(
                    f"   Scope: primeira ocorrencia de {checkpoint['occurrences']} encontrada(s)"
                )
            if checkpoint.get("edit_preview"):
                lines.extend(_format_edit_preview(checkpoint["edit_preview"], "   "))
            if checkpoint.get("diff"):
                lines.append("   Diff:")
                lines.extend(_format_indented_block(checkpoint["diff"], "     "))
            if checkpoint.get("next_step"):
                lines.append(f"   Next: {checkpoint['next_step']}")
            lines.append(f"   Confirm: confirmar checkpoint {checkpoint_id}")
    else:
        lines.append("No pending checkpoints.")

    if checkpoint_events:
        lines.append("")
        lines.append("Recent checkpoint events:")
        for event in checkpoint_events[:5]:
            checkpoint_id = event.get("checkpoint_id", "?")
            label = event.get("label", "unknown")
            status = event.get("status", "unknown")
            reason = event.get("reason")
            suffix = f" ({reason})" if reason else ""
            lines.append(f"- checkpoint {checkpoint_id}: {label} -> {status}{suffix}")
            if event.get("event_detail"):
                lines.append(f"  Detail: {event['event_detail']}")
            context = _format_checkpoint_context(event)
            if context:
                lines.append(f"  Context: {context}")
            if event.get("command"):
                lines.append(f"  Command: {event['command']}")
            if event.get("edit_preview"):
                lines.extend(_format_edit_preview(event["edit_preview"], "  ", max_lines=8))
            if event.get("diff"):
                lines.append("  Diff:")
                lines.extend(_format_indented_block(event["diff"], "    ", max_lines=20))
            if event.get("message"):
                lines.append(f"  {event['message']}")
            if event.get("next_step"):
                lines.append(f"  Next: {event['next_step']}")
    return "\n".join(lines)


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
        command_id = command.get("id", index)
        lines.append(
            f"{index}. #{command_id} {command.get('text', '')} -> "
            f"{action.get('skill', 'unknown')}.{action.get('name', 'unknown')} "
            f"({action.get('status', 'unknown')})"
        )
        history_edit = _history_edit_audit(command)
        if history_edit:
            lines.append(f"   Edit: {history_edit}")
            revert = _history_revert_hint(command)
            if revert:
                lines.append(f"   Revert: {revert}")
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


def format_memory_audit(payload: dict[str, Any]) -> str:
    filters = payload.get("filters", {})
    lines = [
        "[MEMORY AUDIT]",
        f"Generated at: {payload.get('generated_at', 'unknown')}",
        f"Matching commands: {payload.get('matching_count', 0)}",
        f"First command: {payload.get('first_command_at') or 'none'}",
        f"Latest command: {payload.get('latest_command_at') or 'none'}",
    ]
    active_filters = [
        f"{key}={value}"
        for key, value in filters.items()
        if key != "limit" and value
    ]
    if active_filters:
        lines.append(f"Filters: {', '.join(active_filters)}")

    for label, key in (
        ("By intent", "by_intent"),
        ("By skill", "by_skill"),
        ("By action", "by_action"),
        ("By status", "by_status"),
    ):
        items = payload.get(key, [])
        if items:
            lines.append(f"{label}: {_format_counts(items)}")

    sample = payload.get("sample", [])
    if sample:
        lines.append("Sample:")
        for command in sample:
            action = command.get("action", {})
            command_id = command.get("id", "?")
            lines.append(
                f"- #{command_id} {command.get('text', '')} -> "
                f"{action.get('skill', 'unknown')}.{action.get('name', 'unknown')} "
                f"({action.get('status', 'unknown')})"
            )
            history_edit = _history_edit_audit(command)
            if history_edit:
                lines.append(f"  Edit: {history_edit}")
    return "\n".join(lines)


def format_history_delete(payload: dict[str, Any]) -> str:
    lines = [
        "[HISTORY DELETE]",
        f"Status: {payload.get('status', 'unknown')}",
    ]
    if payload.get("reason"):
        lines.append(f"Reason: {payload['reason']}")
    if payload.get("deleted") is not None:
        lines.append(f"Deleted commands: {payload.get('deleted', 0)}")
    if payload.get("selected") is not None:
        lines.append(f"Selected commands: {payload.get('selected', 0)}")
    command_ids = payload.get("command_ids") or []
    if command_ids:
        lines.append(f"Command ids: {', '.join(str(command_id) for command_id in command_ids)}")
    preview = payload.get("preview", {})
    if preview:
        lines.append(f"Preview matches: {preview.get('matching_count', 0)}")
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
    if action.get("name") == "multi_action":
        lines.append(
            "Steps: "
            f"done={action.get('done', 0)} "
            f"needs_confirmation={action.get('needs_confirmation', 0)} "
            f"blocked={action.get('blocked', 0)}"
        )
        checkpoint_ids = action.get("checkpoint_ids") or []
        if checkpoint_ids:
            lines.append(f"Checkpoints: {', '.join(str(checkpoint_id) for checkpoint_id in checkpoint_ids)}")
    if suggestions:
        lines.append("")
        lines.append("Suggestions:")
        lines.extend(f"- {suggestion}" for suggestion in suggestions)
    return "\n".join(lines)


def format_diagnostics(payload: dict[str, Any]) -> str:
    platform = payload.get("platform", {})
    audio = payload.get("audio", {})
    binaries = payload.get("binaries", {})
    python_modules = payload.get("python_modules", {})
    missing = [name for name, item in binaries.items() if not item.get("available")]
    available_count = len(binaries) - len(missing)
    missing_python_modules = [
        name
        for name, item in python_modules.items()
        if not item.get("available")
    ]
    available_python_count = len(python_modules) - len(missing_python_modules)
    lines = [
        "[DIAGNOSTICS]",
        f"System: {platform.get('system', 'unknown')} {platform.get('release', '')}".strip(),
        f"Python: {platform.get('python', 'unknown')}",
        f"Vosk model: {'available' if audio.get('vosk_model_available') else 'missing'}",
        f"Optional binaries: {available_count}/{len(binaries)} available",
        f"Python modules: {available_python_count}/{len(python_modules)} available",
    ]
    if missing:
        lines.append(f"Missing binaries: {', '.join(missing)}")
    if missing_python_modules:
        lines.append(f"Missing Python modules: {', '.join(missing_python_modules)}")
    return "\n".join(lines)


def format_panel(
    presence: dict[str, Any],
    privacy: dict[str, Any],
    history: dict[str, Any],
    diagnostics: dict[str, Any] | None = None,
    checkpoints: dict[str, Any] | None = None,
) -> str:
    sections = [
        format_presence(presence),
        format_checkpoints(checkpoints or presence),
        format_privacy(privacy),
        format_history(history),
    ]
    if diagnostics is not None:
        sections.append(format_diagnostics(diagnostics))
    return "\n\n".join(sections)


def format_ui_state(payload: dict[str, Any]) -> str:
    sections = [
        f"[UI STATE]\nSchema: {payload.get('schema_version', 'unknown')}",
        format_presence(payload.get("presence", {})),
        format_checkpoints(payload.get("checkpoints", {})),
        format_privacy({"data": payload.get("privacy", {})}),
        format_memory_audit(payload.get("memory_audit", {})),
        _format_capabilities(payload.get("capabilities", {})),
        _format_proactive(payload.get("proactive", {})),
        format_history(payload.get("history", {})),
        _format_next_actions(payload.get("actions") or payload.get("next_actions", [])),
    ]
    return "\n\n".join(sections)


def _format_capabilities(payload: dict[str, Any]) -> str:
    actions = payload.get("actions", [])
    commands = payload.get("commands", {})
    state = payload.get("state", {})
    files = state.get("files", {})
    lines = [
        "[CAPABILITIES]",
        f"Project commands: {commands.get('count', 0)}",
        f"Project files: {files.get('tracked_count', 0)}",
        f"Enabled actions: {payload.get('enabled_count', 0)}",
        f"Blocked actions: {payload.get('blocked_count', 0)}",
    ]
    for action in actions[:5]:
        status = "enabled" if action.get("enabled") else f"blocked ({action.get('env_var')})"
        risk = action.get("risk", "low")
        lines.append(f"- {action.get('label', action.get('id', 'unknown'))}: {status} [{risk}]")
    return "\n".join(lines)


def _format_proactive(payload: dict[str, Any]) -> str:
    suggestions = payload.get("suggestions", [])
    lines = ["[PROACTIVE]"]
    if not suggestions:
        lines.append("No proactive suggestions.")
        return "\n".join(lines)

    for suggestion in suggestions[:5]:
        command = suggestion.get("command", suggestion.get("label", "unknown"))
        reason = suggestion.get("reason", "suggested")
        lines.append(f"- {command} ({reason})")
    return "\n".join(lines)


def _format_counts(items: list[dict[str, Any]]) -> str:
    return ", ".join(f"{item.get('name', 'unknown')}={item.get('count', 0)}" for item in items[:5])


def _format_checkpoint_context(item: dict[str, Any]) -> str:
    parts = []
    source = item.get("source_label") or item.get("source")
    if source:
        parts.append(source)
    if item.get("step_index"):
        parts.append(f"step {item['step_index']}")
    if item.get("step_label"):
        parts.append(str(item["step_label"]))
    if item.get("path"):
        parts.append(str(item["path"]))
    return " | ".join(parts)


def _format_indented_block(text: str, prefix: str, max_lines: int = 40) -> list[str]:
    lines = text.splitlines()
    visible = lines[:max_lines]
    formatted = [f"{prefix}{line}" for line in visible]
    if len(lines) > max_lines:
        formatted.append(f"{prefix}... diff truncado ({len(lines) - max_lines} linha(s) restantes)")
    return formatted


def _format_edit_preview(preview: dict[str, Any], prefix: str, max_lines: int = 12) -> list[str]:
    lines = []
    before = preview.get("before")
    after = preview.get("after")
    if before:
        lines.append(f"{prefix}Preview before: {_format_line_span(before)}")
        lines.extend(_format_indented_block(before.get("text", ""), prefix + "  ", max_lines=max_lines))
    if after:
        lines.append(f"{prefix}Preview after: {_format_line_span(after)}")
        lines.extend(_format_indented_block(after.get("text", ""), prefix + "  ", max_lines=max_lines))
    return lines


def _format_line_span(block: dict[str, Any]) -> str:
    start = block.get("line_start")
    end = block.get("line_end")
    focus_start = block.get("focus_start")
    focus_end = block.get("focus_end")
    if start == end:
        window = f"linha {start}"
    else:
        window = f"linhas {start}-{end}"
    if focus_start and focus_end:
        if focus_start == focus_end:
            focus = f"alvo {focus_start}"
        else:
            focus = f"alvo {focus_start}-{focus_end}"
        return f"{window} ({focus})"
    return window


def _history_edit_audit(command: dict[str, Any]) -> str | None:
    audit = _edit_audit_from_command(command)
    if not audit:
        return None
    summary = audit.get("summary")
    if summary:
        return summary
    return audit.get("path")


def _history_revert_hint(command: dict[str, Any]) -> str | None:
    audit = _edit_audit_from_command(command)
    if not audit:
        return None
    return audit.get("revert_command")


def _edit_audit_from_command(command: dict[str, Any]) -> dict[str, Any] | None:
    action = command.get("action", {})
    edit_audit = action.get("edit_audit")
    if isinstance(edit_audit, dict):
        return edit_audit
    delegated = action.get("delegated_action")
    if isinstance(delegated, dict):
        delegated_audit = delegated.get("edit_audit")
        if isinstance(delegated_audit, dict):
            return delegated_audit
    return None


def _format_next_actions(actions: list[Any]) -> str:
    lines = ["[NEXT ACTIONS]"]
    if not actions:
        lines.append("No suggested actions.")
        return "\n".join(lines)
    for action in actions:
        if isinstance(action, dict):
            suffix = " confirm" if action.get("requires_confirmation") else ""
            lines.append(f"- {action.get('label', action.get('command', 'unknown'))} [{action.get('risk', 'low')}{suffix}]")
        else:
            lines.append(f"- {action}")
    return "\n".join(lines)


def _extract_checkpoints(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "checkpoints" in payload:
        return payload.get("checkpoints") or []

    if "automation_checkpoints" in payload:
        return payload.get("automation_checkpoints") or []

    session = payload.get("session", {})
    return session.get("automation_checkpoints") or []


def _extract_checkpoint_events(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if "events" in payload:
        return payload.get("events") or []

    if "automation_checkpoint_events" in payload:
        return payload.get("automation_checkpoint_events") or []

    session = payload.get("session", {})
    return session.get("automation_checkpoint_events") or []
