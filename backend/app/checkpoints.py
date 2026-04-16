from typing import Any


def build_checkpoint_state(session: dict[str, Any]) -> dict[str, Any]:
    checkpoints = session.get("automation_checkpoints", [])
    events = session.get("automation_checkpoint_events", [])
    return {
        "status": "pending" if checkpoints else "empty",
        "pending_count": len(checkpoints),
        "event_count": len(events),
        "checkpoints": checkpoints,
        "events": events,
    }
