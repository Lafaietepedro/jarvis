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
    source = checkpoint.get("source") or ("multi_action" if checkpoint.get("plan") == "multi_action" else "automation")
    step_label = checkpoint.get("step_label") or checkpoint.get("step", {}).get("label") or checkpoint.get("label")
    step_index = checkpoint.get("index")
    path = _checkpoint_value(checkpoint, "path")
    diff = _checkpoint_value(checkpoint, "diff")
    occurrences = _checkpoint_value(checkpoint, "occurrences")
    edit_preview = _checkpoint_value(checkpoint, "edit_preview")
    replacement_strategy = _checkpoint_value(checkpoint, "replacement_strategy")
    return {
        **checkpoint,
        "source": source,
        "source_label": _source_label(source),
        "step_index": step_index,
        "step_label": step_label,
        "path": path,
        "diff": diff,
        "has_diff": bool(diff),
        "occurrences": occurrences,
        "edit_preview": edit_preview,
        "replacement_strategy": replacement_strategy,
        "checkpoint_detail": _checkpoint_detail(source, step_index, step_label, checkpoint),
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
    source = event.get("source") or ("multi_action" if event.get("plan") == "multi_action" else "automation")
    step_index = event.get("step_index") or event.get("index")
    step_label = event.get("step_label") or event.get("label")
    path = _checkpoint_value(event, "path")
    diff = _checkpoint_value(event, "diff")
    edit_preview = _checkpoint_value(event, "edit_preview")
    replacement_strategy = _checkpoint_value(event, "replacement_strategy")
    return {
        **event,
        "source": source,
        "source_label": _source_label(source),
        "step_index": step_index,
        "step_label": step_label,
        "path": path,
        "diff": diff,
        "has_diff": bool(diff),
        "edit_preview": edit_preview,
        "replacement_strategy": replacement_strategy,
        "event_detail": _checkpoint_detail(source, step_index, step_label, event),
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
    if checkpoint.get("source") == "file_edit":
        path = _checkpoint_value(checkpoint, "path")
        occurrences = _checkpoint_value(checkpoint, "occurrences")
        if path:
            if occurrences and occurrences > 1:
                return f"Revisar diff e contexto de `{path}`; apenas a primeira de {occurrences} ocorrencias sera editada."
            return f"Revisar diff de `{path}` antes de confirmar."
    return f"Revisar {checkpoint.get('label', 'checkpoint')} antes de confirmar."


def _source_label(source: str) -> str:
    if source == "multi_action":
        return "pedido composto"
    if source == "file_edit":
        return "edicao de arquivo"
    return "plano de automacao"


def _checkpoint_detail(
    source: str,
    step_index: int | None,
    step_label: str | None,
    checkpoint: dict[str, Any],
) -> str:
    label = _source_label(source)
    parts = [label]
    if step_index:
        parts.append(f"etapa {step_index}")
    if step_label:
        parts.append(step_label)
    reason = checkpoint.get("reason")
    if reason:
        parts.append(reason)
    return " - ".join(parts)


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


def _checkpoint_value(item: dict[str, Any], key: str) -> Any:
    if item.get(key) is not None:
        return item[key]
    return item.get("step", {}).get(key)
