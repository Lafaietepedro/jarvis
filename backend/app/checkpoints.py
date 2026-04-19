from typing import Any

from .risk import classify_checkpoint, permission_for_reason, severity_for_event


def build_checkpoint_state(session: dict[str, Any]) -> dict[str, Any]:
    checkpoints = [_enrich_checkpoint(checkpoint) for checkpoint in session.get("automation_checkpoints", [])]
    events = [_enrich_event(event) for event in session.get("automation_checkpoint_events", [])]
    return {
        "status": "pending" if checkpoints else "empty",
        "pending_count": len(checkpoints),
        "event_count": len(events),
        "summary": _build_summary(checkpoints, events),
        "checkpoints": checkpoints,
        "events": events,
    }


def _build_summary(checkpoints: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    blocked_events = [event for event in events if event.get("status") == "blocked"]
    completed_events = [
        event
        for event in events
        if event.get("status") not in {"blocked", "needs_confirmation", "empty"}
    ]
    latest_event = events[0] if events else None
    return {
        "pending": len(checkpoints),
        "events": len(events),
        "blocked_events": len(blocked_events),
        "completed_events": len(completed_events),
        "latest_status": latest_event.get("status") if latest_event else None,
        "latest_message": latest_event.get("message") if latest_event else None,
        "next_step": _next_step(checkpoints, latest_event),
    }


def _enrich_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    profile = classify_checkpoint(checkpoint)
    return {
        **checkpoint,
        "risk": profile.risk,
        "requires_confirmation": profile.requires_confirmation,
        "permission": profile.permission,
        "risk_reason": profile.reason,
        "risk_category": profile.category,
        "risk_description": profile.description,
        "severity": profile.severity,
        "next_step": _checkpoint_next_step(checkpoint),
    }


def _enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    reason = event.get("reason")
    status = event.get("status", "unknown")
    return {
        **event,
        "severity": severity_for_event(status, reason),
        "message": _event_message(event),
        "next_step": _event_next_step(event),
    }


def _next_step(checkpoints: list[dict[str, Any]], latest_event: dict[str, Any] | None) -> str:
    if checkpoints:
        checkpoint_id = checkpoints[0].get("checkpoint_id")
        return f"Revisar e confirmar checkpoint {checkpoint_id}."
    if latest_event:
        return latest_event.get("next_step", "Nenhuma acao pendente.")
    return "Nenhuma acao pendente."


def _checkpoint_next_step(checkpoint: dict[str, Any]) -> str:
    command = checkpoint.get("command")
    if command:
        return f"Revisar comando `{command}` antes de confirmar."
    return f"Revisar {checkpoint.get('label', 'checkpoint')} antes de confirmar."


def _event_message(event: dict[str, Any]) -> str:
    status = event.get("status", "unknown")
    label = event.get("label", "Checkpoint")
    reason = event.get("reason")
    if status == "blocked":
        return f"{label} foi bloqueado: {reason or 'sem motivo informado'}."
    if status == "done":
        return f"{label} foi concluido."
    return f"{label} terminou com status {status}."


def _event_next_step(event: dict[str, Any]) -> str:
    reason = event.get("reason")
    permission = permission_for_reason(reason)
    if permission:
        return f"Ative {permission}=1 apenas se quiser permitir esse tipo de acao."
    if reason:
        return "Revise a permissao ou ajuste a configuracao antes de tentar novamente."
    return "Nenhuma acao pendente."
